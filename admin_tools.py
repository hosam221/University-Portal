while True:
    print("\n=== System Admin Tools ===")
    print("1. Seed Full System Data")
    print("2. Reset Entire System (DELETE ALL DATA)")
    print("3. Fetch / Print System Data Summary")
    print("4. Create Dean Account")
    print("5. Exit")

    choice = input("Enter your choice: ").strip()

    match choice:
        case "1":
            from services.full_seed import run_full_seed
            run_full_seed()

        case "2":
            confirm = input(
                "⚠️ This will DELETE ALL DATA. Type YES to confirm: "
            ).strip()

            if confirm == "YES":
                from services.reset_system import reset_entire_system
                reset_entire_system()
            else:
                print("❌ Reset cancelled")

        case "3":
            from services.fetch_all_data import fetch_all_data_summary
            fetch_all_data_summary()

        case "4":
            from services.seed_dean import seed_dean_account
            seed_dean_account()

        case "5":
            print("👋 Exiting Admin Tools...")
            break

        case _:
            print("❗ Invalid choice, please try again.")
