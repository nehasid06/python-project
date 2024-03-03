import sqlite3
import getpass
from datetime import datetime

class User:
    def __init__(self, user_id, pin, balance_inr=0):
        self.user_id = user_id
        self.pin = pin
        self.balance_inr = balance_inr

class ATM:
    MAX_LOGIN_ATTEMPTS = 3

    def __init__(self):
        self.conn = sqlite3.connect('atm.db')
        self.create_users_table()
        self.current_user = None

    def create_users_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                      (user_id TEXT PRIMARY KEY, pin TEXT, balance_inr REAL, locked INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                      (user_id TEXT, transaction_type TEXT, amount REAL, timestamp DATETIME)''')
        self.conn.commit()

    def create_account(self):
        user_id = input("Enter your account number: ")
        if self.account_exists(user_id):
            print("Account already exists.")
        else:
            pin = getpass.getpass("Create a PIN for your account: ")
            self.insert_user(user_id, pin)
            print("Account created successfully!")

    def account_exists(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return c.fetchone() is not None

    def insert_user(self, user_id, pin):
        c = self.conn.cursor()
        c.execute("INSERT INTO users (user_id, pin, balance_inr, locked) VALUES (?, ?, 0, 0)",
                  (user_id, pin))
        self.conn.commit()

    def login(self):
        if self.current_user is not None:
            print("Logout the current user before logging in as a different user.")
            return

        user_id = input("Enter your account number: ")
        if not self.account_exists(user_id):
            print("User not found.")
            return

        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()

        if user[3]:  # Check if the user account is locked
            print("Account is locked. Please contact customer support.")
            return

        attempts = 0
        while attempts < self.MAX_LOGIN_ATTEMPTS:
            pin = getpass.getpass("Please enter your PIN: ")
            if pin == user[1]:  # User PIN
                self.current_user = User(user[0], user[1], user[2])
                print("Login successful!")
                return
            else:
                attempts += 1
                print(f"Incorrect PIN. {self.MAX_LOGIN_ATTEMPTS - attempts} attempts remaining.")

        # Lock the account after too many incorrect PIN attempts
        c.execute("UPDATE users SET locked = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()
        print("Login failed. Account locked. Please contact customer support.")

    def record_transaction(self, transaction_type, amount):
        c = self.conn.cursor()
        timestamp = datetime.now()
        c.execute("INSERT INTO transactions (user_id, transaction_type, amount, timestamp) VALUES (?, ?, ?, ?)",
                  (self.current_user.user_id, transaction_type, amount, timestamp))
        self.conn.commit()

    def main_menu(self):
        while True:
            if self.current_user is None:
                print('ATM INTERFACE')
                print('Select an option:')
                print('1. Create Account')
                print('2. Login')
                print('3. Quit')
                response = input('Enter the number of your choice (1/2/3): ')
                if response == '1':
                    self.create_account()
                elif response == '2':
                    self.login()
                elif response == '3':
                    print("Goodbye!")
                    exit()
                else:
                    print('Invalid choice. Please select a valid option.')
            else:
                print('ATM INTERFACE')
                print('Select an option:')
                print('1. TRANSACTIONS HISTORY')
                print('2. WITHDRAW')
                print('3. DEPOSIT')
                print('4. CHANGE PIN')
                print('5. TRANSFER')
                print('6. LOGOUT')
                response = input('Enter the number of your choice (1/2/3/4/5/6): ')

                valid_responses = ['1', '2', '3', '4', '5', '6']
                if response in valid_responses:
                    if response == '1':
                        self.print_statement()
                    elif response == '2':
                        self.withdraw()
                    elif response == '3':
                        self.deposit()
                    elif response == '4':
                        self.change_pin()
                    elif response == '5':
                        self.transfer()
                    elif response == '6':
                        self.logout()
                        print("Goodbye!")
                        break
                else:
                    print('Invalid choice. Please select a valid option.')

    def withdraw(self):
        print('---------------------------------------------')
        print('***************')
        amount = int(input('ENTER AMOUNT YOU WOULD LIKE TO WITHDRAW: '))

        if amount % 10 != 0:
            print('AMOUNT MUST MATCH 10 RUPEE NOTES')
        elif amount > self.current_user.balance_inr:
            print('YOU HAVE INSUFFICIENT BALANCE')
        else:
            self.current_user.balance_inr -= amount
            self.record_transaction("Withdraw", amount)
            print('YOUR NEW BALANCE IS: ', self.current_user.balance_inr, 'RUPEES')

    def deposit(self):
        print()
        print('---------------------------------------------')
        print('***************')
        amount = int(input('ENTER AMOUNT YOU WANT TO LODGE: '))

        if amount % 10 != 0:
            print('AMOUNT MUST MATCH 10 RUPEE NOTES')
        else:
            self.current_user.balance_inr += amount
            self.record_transaction("Deposit", amount)
            print('YOUR NEW BALANCE IS: ', self.current_user.balance_inr, 'RUPEES')

    def change_pin(self):
        print('-----------------------------')
        print('***********')
        new_pin = str(getpass.getpass('ENTER A NEW PIN: '))
        print('***********')
        if new_pin.isdigit() and new_pin != self.current_user.pin and len(new_pin) == 4:
            print('------------------')
            print('******')
            new_ppin = str(getpass.getpass('CONFIRM NEW PIN: '))
            print('*******')
            if new_ppin != new_pin:
                print('------------')
                print('****')
                print('PIN MISMATCH')
                print('****')
                print('------------')
            else:
                c = self.conn.cursor()
                c.execute("UPDATE users SET pin = ? WHERE user_id = ?", (new_pin, self.current_user.user_id))
                self.conn.commit()
                self.current_user.pin = new_pin
                print('NEW PIN SAVED')
        else:
            print('-------------------------------------')
            print('*************')
            print(' NEW PIN MUST CONSIST OF 4 DIGITS \nAND MUST BE DIFFERENT TO THE PREVIOUS PIN')
            print('*************')
            print('-------------------------------------')

    def transfer(self):
        if self.current_user is None:
            print("You must be logged in to transfer money.")
            return

        source_account = input("Enter your account number: ")
        destination_account = input("Enter the destination account number: ")
        amount = int(input("Enter the amount to transfer: "))

        if amount % 10 != 0:
            print('AMOUNT MUST MATCH 10 RUPEE NOTES')
        elif amount > self.current_user.balance_inr:
            print('YOU HAVE INSUFFICIENT BALANCE')
        else:
            destination_user = self.get_user_by_id(destination_account)
            if destination_user is not None:
                self.current_user.balance_inr -= amount
                self.record_transaction("Transfer (Out)", amount)

                destination_user.balance_inr += amount
                self.record_transaction("Transfer (In)", amount)
                print('TRANSFER SUCCESSFUL')
            else:
                print('DESTINATION ACCOUNT NOT FOUND')

    def print_statement(self):
        print('-----------------------------')
        print('***********')
        print(str.capitalize(self.current_user.user_id), 'YOU HAVE ', self.current_user.balance_inr, 'RUPEES ON YOUR ACCOUNT.')
        print('***********')
        print('-----------------------------')
        self.record_transaction("Statement", 0)

    def logout(self):
        self.current_user = None
        print("Logged out successfully!")

    def get_user_by_id(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        else:
            return None

# Create the 'atm.db' database file and tables
conn = sqlite3.connect('atm.db')
conn.close()

# Create an instance of the ATM class
atm = ATM()

# Run the ATM program
while True:
    print('-------------------------')
    print('*********')
    response = input('SELECT FROM FOLLOWING OPTIONS: \n'
                     'Create Account (C) \n'
                     'Login (L) \n'
                     'Quit (Q) \n'
                     'Type The Letter Of Your Choices: ').lower()
    print('*********')
    print('-------------------------')

    valid_responses = ['c', 'l', 'q']
    response = response.lower()
    if response == 'c':
        atm.create_account()
    elif response == 'l':
        atm.login()
        atm.main_menu()
    elif response == 'q':
        print("Goodbye!")
        exit()
    else:
        print('------------------')
        print('******')