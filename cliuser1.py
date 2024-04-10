import argparse

import requests

MyIP = "http://127.0.0.1:5001"


def main():
    parser = argparse.ArgumentParser(description='Create a transaction')
    parser.add_argument('-t', '--transaction', nargs='+',
                        help='Create a transaction in the format: -t <address> <message>')

    parser.add_argument('--address', type=int, help='Address of the recipient')
    parser.add_argument('--message', help='Message')

    parser.add_argument('-stake', '--stake_amount', nargs='+',
                        help='Stake amount in format: -stake <amount>')
    parser.add_argument('action', nargs='?', default=None, help='Action to perform (view)')
    args = parser.parse_args()
    if args.transaction:
        if len(args.transaction) != 2:
            parser.error("Argument -t/--transaction requires exactly 2 values: address and message")
        else:
            address, message = args.transaction

            params = {
                "address": address,
                "message": message
            }

            response = requests.post(MyIP + "/create_transaction", json=params)
            if response.json() == 200:
                print("Transaction created successfully.")
            elif response.json() == 400:
                print("wrong signature")
            elif response.json() == 401:
                print("you dont have money")
            elif response.json() == 402:
                print("you dont have the permission to do this")
            elif response.json() == 403:
                print("Wrong previous hash")
            elif response.json() == 404:
                print("wrong validator")

    elif args.stake_amount:
        if len(args.stake_amount) != 1:
            parser.error("Argument -stake/--stake_amount requires exactly 1 value: amount")
        else:
            amount = args.stake_amount
            params = {
                "amount": amount
            }

            response = requests.post(MyIP + "/stake", json=params)

            if response.json() == 200:
                print("Stake created successfully.")
            elif response.json() == 400:
                print("wrong signature")
            elif response.json() == 401:
                print("you dont have money")
            elif response.json() == 402:
                print("you dont have the permission to do this")
            elif response.json() == 403:
                print("Wrong previous hash")
            elif response.json() == 404:
                print("wrong validator")

    if args.action == 'view':
        response = requests.get(MyIP + "/view")
        print(response.json())

    elif args.action == 'balance':
        response = requests.get(MyIP + "/balance")
        print(response.json())

    elif args.action == 'help':
        print("Options: ")
        print("-t <recipient_address> <message> -> send BCC (real number) or a message(string), using "" ")
        print("-stake <amount> -> create a stake amount")
        print("view -> shows the transactions of the last block as well as the validator")
        print("balance -> shows the remaining balance of the node")
        print("help -> shows this help message")


if __name__ == "__main__":
    main()
