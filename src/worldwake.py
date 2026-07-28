def determine_consequence(event: str, days_passed: int) -> str:
    """Create a simple consequence based on the campaign event."""

    event_lower = event.lower()

    if "king" in event_lower or "queen" in event_lower:
        return (
            f"After {days_passed} days, rumors surrounding the crown have "
            "spread into neighboring settlements. Local leaders are beginning "
            "to choose sides."
        )

    if "monster" in event_lower or "dragon" in event_lower:
        return (
            f"After {days_passed} days, travelers have started avoiding the "
            "region. Trade slows, prices rise, and hunters begin organizing."
        )

    if "village" in event_lower or "town" in event_lower:
        return (
            f"After {days_passed} days, news of the event reaches nearby "
            "communities. Some residents prepare to leave while others arrive "
            "to investigate."
        )

    return (
        f"After {days_passed} days, the event begins producing quiet ripples "
        "through the world. Someone has noticed, although their intentions "
        "remain unknown."
    )


def main() -> None:
    print("\nWORLDWAKE")
    print("The world continues, even when the party is elsewhere.\n")

    event = input("What happened in the campaign? ")

    while True:
        days_text = input("How many days have passed? ")

        try:
            days_passed = int(days_text)

            if days_passed < 0:
                print("Please enter zero or a positive number.")
                continue

            break
        except ValueError:
            print("Please enter a whole number, such as 3 or 14.")

    consequence = determine_consequence(event, days_passed)

    print("\nWORLD UPDATE")
    print(consequence)


if __name__ == "__main__":
    main()