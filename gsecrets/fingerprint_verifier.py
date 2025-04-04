from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
from typing import Any, cast

from gi.repository import Gio, GLib

BUS_NAME = "net.reactivated.Fprint"
DBUS_TIMEOUT = 500  # In milliseconds
VERIFY_STATUS_TUPLE = 2


class FingerprintVerifier:
    """Provides easy access to a fingerprint device."""

    def __init__(
        self,
        on_success: Callable,
        on_retry: Callable,
        on_failure: Callable,
    ) -> None:
        """Constructor.

        Might throw an exception if dbus is unavailable, fprintd is missing or
        no device is available.

        Arguments:
        ---------
            on_success: Function to be called on success.
            on_retry: Function to be called if the fingerprint sensor suggests retrying.
            on_failure: Function to be called if the fingerprint did not match or the
                        hardware refused in the process.

        """
        self.on_success = on_success
        self.on_retry = on_retry
        self.on_failure = on_failure

        self._is_claimed = False
        self._device_proxy = None
        self._signal = None

    def connect(self, cb: Gio.Callback) -> None:
        """Initializes the connection to the fingerprint device.

        Shouldn't be called manually unless disconnect was called on the object before.

        Might throw an exception if dbus is unavailable, fprindt is missing
        or no device is available.
        """
        if self._is_claimed:
            return

        async def connect_fingerprint():
            con = await Gio.bus_get(Gio.BusType.SYSTEM, None)

            manager_proxy = await Gio.DBusProxy.new(
                con,
                Gio.DBusProxyFlags.NONE,
                None,
                BUS_NAME,
                "/net/reactivated/Fprint/Manager",
                "net.reactivated.Fprint.Manager",
                None,
            )
            if manager_proxy is None:
                logging.debug("Fprintd not available.")
                return

            try:
                variant = await manager_proxy.call(
                    "GetDefaultDevice",
                    None,
                    Gio.DBusCallFlags.NO_AUTO_START,
                    DBUS_TIMEOUT,
                    None,
                )
                device_str = variant[0]
            except GLib.GError:
                logging.exception("Failed to get default fingerprint device")
                return

            if device_str == "":
                logging.debug("No fingerprint sensor found!")
                return

            self._device_proxy = await Gio.DBusProxy.new(
                con,
                Gio.DBusProxyFlags.NONE,
                None,
                BUS_NAME,
                device_str,
                "net.reactivated.Fprint.Device",
                None,
            )
            if self._device_proxy is None:
                logging.debug("Failed to find the default fingerprint device.")
                return

            self._signal = self._device_proxy.connect("g-signal", self._signal_handler)
            logging.debug("Successfully connected to the fingerprint device.")

            cb()

        app = Gio.Application.get_default()
        app.create_asyncio_task(connect_fingerprint())

    def disconnect(self) -> None:
        """Removes the handlers from the signal.

        Should be called when the class is not needed anymore.
        """
        if self._is_claimed or self._device_proxy is None:
            return

        self._is_claimed = False
        self._device_proxy.disconnect(self._signal)
        self._signal = None
        self._device_proxy = None
        logging.debug("Disconnected from the fingerprint device.")

    async def verify_start(self) -> bool:
        """Starts the fingerprint verification process.

        Returns: True if the fingerprint verification started.

        """
        if self._device_proxy is None:
            return False

        try:
            await self._claim_device()
        except GLib.Error:
            logging.exception("Failed to claim device")
            return False

        self._is_claimed = True
        try:
            await self._verify_start()
        except GLib.Error:
            logging.exception("Failed to start fingerprint verification on the device")
            return False

        logging.debug("Claimed fingerprint device, verification ongoing...")
        return True

    async def verify_stop(self) -> None:
        """Stops the fingerprint verification process."""
        if not self._is_claimed:
            return

        self._is_claimed = False

        try:
            await self._verify_stop()
            await self._release_device()
            logging.debug("Stopped verification, released fingerprint device.")
        except GLib.Error as err:
            logging.debug("Exception while releasing fingerprint device: %s", err)

    #
    # Internal methods
    #

    async def _claim_device(self) -> None:
        if self._device_proxy:
            await self._device_proxy.call(
                "Claim",
                GLib.Variant("(s)", ("",)),
                Gio.DBusCallFlags.NO_AUTO_START,
                DBUS_TIMEOUT,
                None,
            )

    async def _release_device(self) -> None:
        if self._device_proxy:
            await self._device_proxy.call(
                "Release",
                None,
                Gio.DBusCallFlags.NO_AUTO_START,
                DBUS_TIMEOUT,
                None,
            )

    async def _verify_start(self) -> None:
        if self._device_proxy:
            await self._device_proxy.call(
                "VerifyStart",
                GLib.Variant("(s)", ("any",)),
                Gio.DBusCallFlags.NO_AUTO_START,
                DBUS_TIMEOUT,
                None,
            )

    async def _verify_stop(self) -> None:
        if self._device_proxy:
            await self._device_proxy.call(
                "VerifyStop",
                None,
                Gio.DBusCallFlags.NO_AUTO_START,
                DBUS_TIMEOUT,
                None,
            )

    retry_results = [
        "verify-retry-scan",
        "verify-swipe-too-short",
        "verify-finger-not-centered",
        "verify-remove-and-retry",
    ]

    def _signal_handler(
        self,
        _proxy: Gio.DBusProxy,
        _sender: str,  # pylint: disable=unused-argument
        signal: str,
        args: tuple[Any],
    ) -> None:
        if signal != "VerifyStatus" or len(args) != VERIFY_STATUS_TUPLE:
            return

        result, done = cast(tuple[str, bool], args)  # see mypy/issues/1178

        if result in self.retry_results and not done:
            self.on_retry()

        if done:
            if result != "verify-disconnected":
                app = Gio.Application.get_default()
                app.create_asyncio_task(self.verify_stop())

            if result == "verify-match":
                self.on_success()
            else:
                self.on_failure()
