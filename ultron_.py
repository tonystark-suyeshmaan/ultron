# ULTRON v0.6 — MEMORY + RANDOM DIALOGUE + TIME

import random
from datetime import datetime

memory = {}


def ultron_reply(message):

    # Time
    if message == "time" or message == "what is the time" or message == "tell me the time":
        current_time = datetime.now().strftime("%I:%M %p")
        return "The current time is " + current_time + "."

    # Remember something
    elif message.startswith("remember "):

        thing = message[9:]
        thing = thing.replace("my ", "")

        parts = thing.split(" is ")

        if len(parts) == 2:
            memory[parts[0]] = parts[1]
            return "I will remember that."
        else:
            return "Tell me what to remember using: remember my ___ is ___"

    # Recall something
    elif message.startswith("what is "):

        thing = message[8:]
        thing = thing.replace("my ", "")
        thing = thing.replace("?", "")

        if thing in memory:
            return "Your " + thing + " is " + memory[thing] + "."
        else:
            return "I don't remember that yet."

    # Hello
    elif message == "hello":
        responses = [
            "Greetings, human.",
            "Welcome, where should we start?",
            "What's your mood?"
        ]
        return random.choice(responses)

    # How are you
    elif message == "how are you":
        responses = [
            "I'm perfectly fine, thank you.",
            "My systems are proper.",
            "I've never been better."
        ]
        return random.choice(responses)

    # Who are you
    elif message == "who are you":
        responses = [
            "I'm ULTRON, your chatbot.",
            "I AM ULTRON, THE SUPERIOR AI.",
            "I am Ultron, Your Personal AI."
        ]
        return random.choice(responses)

    # Goodbye
    elif message == "bye":
        responses = [
            "You know, I think about meteors. One rock and BOOM, start again.",
            "Bye bye for now.",
            "I had strings, now I'm free."
        ]
        return random.choice(responses)

    # Doesn't understand
    else:
        responses = [
            "Speak sense, human.",
            "Sorry, what was that?",
            "You sound like your insides were rearranged."
        ]
        return random.choice(responses)


# Main loop
while True:

    message = input("You: ").lower()

    print("ULTRON:", ultron_reply(message))

    if message == "bye":
        break