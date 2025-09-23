#!/usr/bin/python3                                                                                                                                                                       
from datetime import datetime, timedelta
from importlib import reload
from scamper import ScamperCtrl, ScamperFile, ScamperTrace
import argparse
import logging
import os
import uuid

OPEN_RESOLVERS_TO_TRACERT = [ 
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9"
]

LOG_DIRECTORY = "logs"
LOG_PREFIX = "aims18-hackathon-traceroute-demo"

# Helper function to setup logging
def setup_logging():

    # Setup logging
    reload(logging)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Make logs dir on disk, if necessary
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    # File path for logger output to disk
    fhandler_path = os.path.join(LOG_DIRECTORY, "{}-{}.log".format(LOG_PREFIX, datetime.now().date().isoformat()))

    # File handler
    fhandler_dbg = logging.FileHandler(filename=fhandler_path, mode="a")
    fhandler_dbg.setLevel(logging.DEBUG)

    # Console handler
    chandler = logging.StreamHandler()
    chandler.setLevel(logging.INFO)

    # Create formatter and add it to handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fhandler_dbg.setFormatter(formatter)
    chandler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(fhandler_dbg)
    logger.addHandler(chandler)                                                                                                                                                          

    logger.debug(f"Logger initialized: '{fhandler_path}'")

def probe(mux):

    LOGGER = logging.getLogger(__name__)

    # Create output file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data-tracert/{timestamp}_{uuid.uuid4()}.warts"

    LOGGER.info(f"Starting measurement and saving data to: {output_file}")

    # Open warts file for writing
    with ScamperFile(output_file, "w") as outfile:

        # Connect to scamper daemon and attach output file
        with ScamperCtrl(mux=mux, outfile=outfile) as ctrl:
        
            ctrl.add_vps(ctrl.vps())

            # Do the traceroute measurements
            for i_address in OPEN_RESOLVERS_TO_TRACERT:
                ctrl.do_trace(i_address, method='icmp-paris', inst=ctrl.instances())

            # Wait for response
            for i_object in ctrl.responses(timeout=timedelta(seconds=180)):
                if isinstance(i_object, ScamperTrace):
                    if i_object.hop_count:
                        LOGGER.info(f"Trace result: {i_object.inst.ipv4} ({i_object.inst.name}) -> {i_object.dst}: {i_object.hop_count} hops")
                    else:
                        LOGGER.info(f"No response from {i_object.inst.name} ({i_object.inst.ipv4}) to {i_object.dst}")
            else:
                LOGGER.warning(f"No (more) response(s)")
                                                                                                                                                                                         
    LOGGER.info(f"Data saved to: {output_file}")


def main():

    parser = argparse.ArgumentParser(
        description="Python script to perform Ark open resolver ping measurements."
    )
    parser.add_argument("mux", help="Path to Scamper mux socket")


    args = parser.parse_args()

    setup_logging()
    probe(args.mux)

if __name__ == "__main__":
    main()
