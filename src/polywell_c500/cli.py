import argparse
from .display import C500Display

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="/dev/ttyUSB0")
    parser.add_argument("--listen", action="store_true")
    parser.add_argument("--center", action="store_true")
    parser.add_argument("--row", type=int)
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()

    with C500Display(args.device) as display:
        if args.listen:
            try:
                while True:
                    print(display.wait_button().button.value)
            except KeyboardInterrupt:
                return 0

        message = " ".join(args.message)

        if args.row:
            display.initialize()
            display.write_row(args.row, message)
        else:
            display.show(message.split("~"), initialize=True, center=args.center)

    return 0
