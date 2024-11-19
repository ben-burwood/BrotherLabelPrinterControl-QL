from dataclasses import dataclass
from logging import Logger

from .outcome import PrintOutcome


@dataclass
class SendStatus:
    instructions_sent: bool = True  # The instructions were sent to the printer.
    outcome: PrintOutcome = PrintOutcome.UNKNOWN
    printer_state: dict = None  # If the selected backend supports reading back the printer state, this key will contain it.
    did_print: bool = False  # If True, a print was produced. It defaults to False if the outcome is uncertain (due to a backend without read-back capability).
    ready_for_next_job: bool = False  # If True, the printer is ready to receive the next instructions. It defaults to False if the state is unknown.

    def log_status(self, logger: Logger) -> None:
        if not self.did_print:
            logger.warning("'printing completed' status not received.")
        if not self.ready_for_next_job:
            logger.warning("'waiting to receive' status not received.")
        if (not self.did_print) or (not self.ready_for_next_job):
            logger.warning("Printing potentially not successful?")
        if self.did_print and self.ready_for_next_job:
            logger.info("Printing was successful. Waiting for the next job.")
