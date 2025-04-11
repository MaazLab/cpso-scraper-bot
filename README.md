# CPSO Doctor Scraper 🩺

A Python-based web scraper that extracts publicly available doctor information from the [College of Physicians and Surgeons of Ontario (CPSO)](https://www.cpso.on.ca/) website. The scraper automates browsing and scraping using Selenium and BeautifulSoup, capturing key details such as doctor name, specialties, locations, contact numbers, and fax.

---

## 🚀 Features

- ✅ Automated scraping using Selenium and BeautifulSoup
- ✅ Extracts doctor details:
  - Name
  - Specialty
  - Practice Locations
  - Phone Numbers
  - Fax Numbers
- ✅ Saves data for further processing or analysis
- ✅ Easily customizable search criteria

---

## 🛠️ Tech Stack

- Python 3.x
- [Selenium](https://selenium.dev/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- ChromeDriver (or any WebDriver)

---

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MaazLab/cpso-scraper-bot.git
   cd cpso-doctor-scraper

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

---

## 🧪 Usage
  Update the search parameters in the script (e.g., `keywords`, `location`, `page limits`), then run:
  ```bash
  python cpso_scraper.py
```
The results will be printed to the console or saved to a CSV/JSON file (depending on your implementation).

---

## 📁 Output Format
  Each doctor record includes:
  ```bash
      {
    "Name": "Dr. Jane Doe",
    "Specialization": ["Family Medicine"],
    "Locations": ["123 Health St, Toronto, ON"],
    "Phone": [123-456-7890],
    "Fax": [123-456-7891]
    }
```
---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## ✨ Author
**Maaz Rafiq** <br>
[GitHub](https://github.com/MaazLab/) | [LinkedIn](https://www.linkedin.com/in/maaz-rafiq/)

   
