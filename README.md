# etsy-2-moneybird

Etsy to Moneybird Invoice Converter

I'm mainly selling on other platforms but have the occasional sale on Etsy. I was looking for a way to get my Etsy sales to Moneybird without too much hassle. This was easier/quicker than understanding their API.

This web application automatically processes Etsy invoice PDFs and creates corresponding invoices in Moneybird with contacts, products, shipping costs, and marks them as paid.

## Features

- Upload Etsy invoice PDFs via web interface
- Automatic contact extraction and creation in Moneybird
- Invoice generation
- Automatic marking as sent and paid
- Configurable tax rates, ledger accounts, and document styles

## Requirements

- Python 3.7+
- Moneybird account with API access
- The following Python packages (see requirements.txt):
  - Flask
  - PyPDF2
  - requests
  - python-dotenv
  - gunicorn (for production)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/dennisklappe/etsy-2-moneybird.git
cd etsy-2-moneybird
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the environment file and configure your settings:
```bash
cp .env.example .env
```

4. Edit `.env` with your Moneybird API credentials:
```bash
# Get these from your Moneybird account
MONEYBIRD_API_TOKEN=your_api_token_here
MONEYBIRD_ADMIN_ID=your_administration_id_here

# Get these IDs from your Moneybird setup
TAX_RATE_ID=your_tax_rate_id
LEDGER_ACCOUNT_ID=your_ledger_account_id
PROJECT_ID=your_project_id
DOCUMENT_STYLE_ID=your_document_style_id
```

## Getting Moneybird Configuration IDs

All IDs can be found in the URL when editing the respective item in Moneybird. Look for the number after the last slash in URLs like `https://moneybird.com/xxxxxxxxxx/item_type/yyyyyyyyyy/edit` - the `yyyyyyyyyy` is your ID.

### API Token and Administration ID
1. Go to Moneybird Settings > API & Integrations: `https://moneybird.com/xxxxxxxxxx/oauth_authorizations`
2. Create a new API token
3. Note your Administration ID from the URL (the `xxxxxxxxxx` part)

### Tax Rate ID
1. Go to Tax Rates: `https://moneybird.com/xxxxxxxxxx/tax_rates`
2. Find or create the correct tax rate for sales invoices
3. Click your tax rate to edit it: `https://moneybird.com/xxxxxxxxxx/tax_rates/yyyyyyyyyy/edit`
4. The `yyyyyyyyyy` in the URL is your Tax Rate ID

### Ledger Account ID
1. Go to Chart of Accounts: `https://moneybird.com/xxxxxxxxxx/ledger_accounts`
2. Click or create the correct category for your sales
3. Edit URL will be: `https://moneybird.com/xxxxxxxxxx/ledger_accounts/yyyyyyyyyy/edit`
4. The `yyyyyyyyyy` is your Ledger Account ID

### Project ID
1. Go to Projects: `https://moneybird.com/xxxxxxxxxx/projects`
2. Find or create your project for Etsy sales
3. Click your project to edit: `https://moneybird.com/xxxxxxxxxx/projects/yyyyyyyyyy/edit`
4. The `yyyyyyyyyy` is your Project ID

### Document Style ID
1. Go to Document Styles: `https://moneybird.com/xxxxxxxxxx/document_styles`
2. Find or create the correct document template/style
3. Click to edit: `https://moneybird.com/xxxxxxxxxx/document_styles/yyyyyyyyyy/edit`
4. The `yyyyyyyyyy` is your Document Style ID

## Usage

### Development
```bash
python webapp.py
```

### Production with Gunicorn
```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 webapp:app
```

### Production with Systemd (Linux)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/etsy-2-moneybird.service
```

```ini
[Unit]
Description=Etsy to Moneybird Converter Web Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/etsy-2-moneybird
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 webapp:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable etsy-2-moneybird
sudo systemctl start etsy-2-moneybird
```

## How It Works

1. Upload an Etsy invoice PDF through the web interface
2. The application extracts text and parses:
   - Customer contact information (name, address, email)
   - Order details (number, date, products, shipping)
3. Creates or finds existing contact in Moneybird
4. Generates invoice with:
   - Product lines with correct quantities and prices
   - Shipping costs
   - Tax-inclusive pricing
   - Your configured document style and project
5. Marks invoice as sent and paid automatically

## Project Structure

```
etsy-2-moneybird/
├── etsy_parser.py       # Core parsing and Moneybird integration logic
├── webapp.py            # Flask web interface  
├── templates/           # HTML templates for web interface
├── .env                 # Environment configuration (not in git)
├── .env.example         # Example environment file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Language Requirements

**Important**: This application currently only works with Etsy invoices in **English**. The parsing logic looks for English keywords like "Deliver to", "Order date", "Order #". If your Etsy account is set to another language, you'll need to change it to English in your Etsy account settings before generating invoices.


## Configuration

All configuration is handled through environment variables in the `.env` file:

- `MONEYBIRD_API_TOKEN`: Your Moneybird API token
- `MONEYBIRD_ADMIN_ID`: Your Moneybird administration ID
- `TAX_RATE_ID`: Tax rate
- `LEDGER_ACCOUNT_ID`: Sales ledger account
- `PROJECT_ID`: Project to assign invoices to
- `DOCUMENT_STYLE_ID`: Invoice template/style
- `FLASK_HOST`: Host to bind to (default: 0.0.0.0)
- `FLASK_PORT`: Port to run on (default: 5000)

## License

MIT License - feel free to modify and use as needed.

## Contributing

Pull requests welcome. For major changes, please open an issue first to discuss what you would like to change.