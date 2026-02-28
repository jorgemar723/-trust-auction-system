from src.database.register_user import register_user


def main():
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    result = register_user(email, password)
    print(result)


if __name__ == "__main__":
    main()