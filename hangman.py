import customtkinter as ctk
from tkinter import messagebox  # Import tkinter messagebox
import random


class HangmanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Hangman Game")
        self.root.geometry("1000x800")

        # Set up the game words and hints
        self.words_with_hints = [
            ("APPLE", "A fruit often associated with health."),
            ("HOUSE", "A place where people live."),
            ("PLANE", "A flying vehicle."),
            ("BRICK", "A basic building material."),
            ("CHAIR", "You sit on it."),
            ("PIZZA", "A popular Italian dish."),
            ("CLOUD", "White and fluffy in the sky."),
            ("TRAIN", "Runs on tracks."),
            ("BREAD", "Basic food made from flour."),
            ("PHONE", "Used for communication.")
        ]

        # Choose a random word and hint
        self.word, self.hint = random.choice(self.words_with_hints)
        self.display_word = ["_"] * len(self.word)
        self.guessed_letters = set()
        self.attempts_left = 6

        # Title Label
        self.title_label = ctk.CTkLabel(root, text="Hangman Game", font=("Arial", 24, "bold"))
        self.title_label.pack(pady=10)

        # Hint Display
        self.hint_label = ctk.CTkLabel(root, text=f"Hint: {self.hint}", font=("Arial", 16, "italic"))
        self.hint_label.pack(pady=10)

        # Word Display
        self.word_display = ctk.CTkLabel(
            root, text=" ".join(self.display_word), font=("Arial", 20, "bold")
        )
        self.word_display.pack(pady=20)

        # Hangman Canvas
        self.hangman_canvas = ctk.CTkCanvas(root, width=300, height=400, bg="white", highlightthickness=0)
        self.hangman_canvas.pack(pady=10)
        self.draw_hangman(0)  # Draw the initial empty hangman frame

        # Letter Buttons Frame
        self.buttons_frame = ctk.CTkFrame(root)
        self.buttons_frame.pack(pady=20)

        self.create_letter_buttons()

        # Reset Button
        self.reset_button = ctk.CTkButton(root, text="Restart Game", command=self.reset_game)
        self.reset_button.pack(pady=20)

    def create_letter_buttons(self):
        """Create buttons for each letter of the alphabet."""
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            btn = ctk.CTkButton(
                self.buttons_frame,
                text=letter,
                width=40,
                height=40,
                font=("Arial", 14),
                command=lambda l=letter: self.make_guess(l),
            )
            btn.grid(row=i // 9, column=i % 9, padx=5, pady=5)

    def make_guess(self, letter):
        """Handle a guessed letter."""
        if letter in self.guessed_letters:
            return  # Ignore already guessed letters

        self.guessed_letters.add(letter)

        if letter in self.word:
            for i, char in enumerate(self.word):
                if char == letter:
                    self.display_word[i] = letter
            self.word_display.configure(text=" ".join(self.display_word))
        else:
            self.attempts_left -= 1
            self.draw_hangman(6 - self.attempts_left)  # Update the hangman drawing

        self.check_game_status()

    def check_game_status(self):
        """Check if the player has won, lost, or the game is ongoing."""
        if "_" not in self.display_word:
            self.show_end_message("Congratulations! You've won!")
        elif self.attempts_left <= 0:
            self.show_end_message(f"Game Over! The word was: {self.word}")

    def draw_hangman(self, step):
        """Draw the hangman step by step."""
        self.hangman_canvas.delete("all")  # Clear the canvas

        # Hangman frame
        if step >= 0:
            self.hangman_canvas.create_line(50, 350, 250, 350, width=4)  # Base
            self.hangman_canvas.create_line(150, 350, 150, 50, width=4)   # Pole
            self.hangman_canvas.create_line(150, 50, 200, 50, width=4)    # Top beam
            self.hangman_canvas.create_line(200, 50, 200, 100, width=4)   # Rope

        # Hangman body parts
        if step >= 1:
            self.hangman_canvas.create_oval(180, 100, 220, 140, width=4)  # Head
        if step >= 2:
            self.hangman_canvas.create_line(200, 140, 200, 220, width=4)  # Body
        if step >= 3:
            self.hangman_canvas.create_line(200, 160, 170, 190, width=4)  # Left arm
        if step >= 4:
            self.hangman_canvas.create_line(200, 160, 230, 190, width=4)  # Right arm
        if step >= 5:
            self.hangman_canvas.create_line(200, 220, 170, 270, width=4)  # Left leg
        if step >= 6:
            self.hangman_canvas.create_line(200, 220, 230, 270, width=4)  # Right leg

    def show_end_message(self, message):
        """Display an end-of-game message and disable letter buttons."""
        messagebox.showinfo("Game Over", message)
        self.disable_buttons()

    def disable_buttons(self):
        """Disable all letter buttons after the game ends."""
        for widget in self.buttons_frame.winfo_children():
            widget.configure(state="disabled")

    def reset_game(self):
        """Reset the game to its initial state."""
        self.word, self.hint = random.choice(self.words_with_hints)
        self.display_word = ["_"] * len(self.word)
        self.guessed_letters = set()
        self.attempts_left = 6

        self.hint_label.configure(text=f"Hint: {self.hint}")
        self.word_display.configure(text=" ".join(self.display_word))
        self.draw_hangman(0)  # Reset hangman drawing

        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        self.create_letter_buttons()


def main():
    """Main function to run the Hangman game."""
    root = ctk.CTk()
    app = HangmanGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
