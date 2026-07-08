
# QuoteBot
Quick Telegram bot for user messages quotation with customization support.



## Features

- Message-based quotes: Generates quotes directly from user messages.
- Pre-configured quote pool: Reads a formatted file set up in your config and displays a random quote from it via command.
- Fully customizable: Quick and easy setup to personalize the quote's appearance.
- On-demand random quotes: Displays a random quote from the current chat using a specific command.


## Installation

1. Create a virtual environment using your tool of choice.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create copy of `config.example.yaml` file, rename it to `config.yaml` and fill in your bot credentials.
4. Run the application and enjoy!
```bash
py main.py
```

## Usage

1. `/quote` (without replying to a message)  
Sends a random quote from the current chat history.

2. `/quote` (as a reply to a message)  
Generates a quote from the replied-to message and sends it.

3. `/wise`  
Displays a random quote from your pre-configured file.
## Customization

To create a new custom skin for the bot, copy the `default` folder inside the `skins` directory, rename it, and modify its contents.

### Skin Configuration Breakdown

Each skin contains a configuration file that defines the layout and styling. Here is what the parameters mean:

#### Background
* `filename`: The background image file name.
* `left_top`: The `[x, y]` coordinates for the top-left corner of the text bounding box.
* `right_bottom`: The `[x, y]` coordinates for the bottom-right corner of the text bounding box.

#### Userpic (Avatar)
* `filename`: The placeholder image name used if a user profile picture is unavailable.
* `location`: The `[x, y]` coordinates for the top-left corner of the avatar.
* `radius`: The radius of the avatar circle.
* `border_color`: The border color in `[R, G, B, A]` format.
* `border_radius`: The thickness of the avatar border.

#### Username
* `align`: Text alignment for the username relatively to userpic (`left` or `right`).
* `color`: The color of the username text (supports standard color names or hex codes).

#### Font
* `filename`: The `.ttf` font file name placed inside the skin folder.
* `color`: The color of the quote text.
