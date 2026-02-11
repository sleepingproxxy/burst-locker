# 📱 Burst Blocker - Telegram Report Tool

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version 1.0.0"/>
  <img src="https://img.shields.io/badge/python-3.7+-green.svg" alt="Python 3.7+"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License MIT"/>
  <img src="https://img.shields.io/badge/Telegram-API-blue?logo=telegram" alt="Telegram API"/>
  <img src="https://img.shields.io/badge/Tor-SOCKS5-7D4698?logo=tor" alt="Tor SOCKS5"/>
</p>

<p align="center">
  <b>A powerful tool for reporting spam, abuse, and policy violations on Telegram</b><br>
  <i>Report with multiple reasons, burst mode, and Tor IP rotation</i>
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Available Report Reasons](#-available-report-reasons)
- [Tor Integration](#-tor-integration)
- [License](#-license)
- [Disclaimer](#-disclaimer)

---

## ✨ Features
 ____________________________________________________________________________________
| Feature                     | Description                                          |
|-----------------------------|------------------------------------------------------|
| 🎯 **3 Report Modes**      | Single, Burst (multiple reasons), Full (all reasons)  |
| 🔄 **IP Rotation**         | Automatic Tor IP switching with configurable interval |
| 🕵️ **User-Agent Rotation** | Random User-Agent headers for API requests            |
| 📊 **Bulk Reporting**      | Configurable number of reports per reason             |
| 🌐 **SOCKS5 Proxy**        | Full Tor proxy support                                |
| 🧪 **Test Mode**           | Dry-run without actual reporting                      |
| 🛡️ **10+ Report Reasons**  | All official Telegram report categories               |
|____________________________________________________________________________________|
---

## 🔧 Installation

### Prerequisites

- Python 3.7 or higher
- Telegram API credentials ([my.telegram.org](https://my.telegram.org))
- (Optional) Tor service for IP rotation

### Setup

```bash
# Clone repository
git clone https://github.com/sleepingproxxy/burst-blocker.git
cd burst-blocker

# Install dependencies
pip install -r requirements.txt

# For Tor IP switching (optional)
pip install stem
```




## 🚀 Quick Start

### 1. Get Telegram API Credentials

1. Visit [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Go to "API Development Tools"
4. Create new application
5. Copy `api_id` and `api_hash`

### 2. Basic Usage

```bash
# Report spammer with 5 reports
python burst_blocker.py \
  --api_id 1234567 \
  --api_hash abcdef123456789 \
  --target @spammer_username \
  --reason spam \
  --count 5
```



## 📚 Usage Examples

### Single Mode - One Reason
```bash
python burst_blocker.py \
  --api_id 12345 \
  --api_hash abcdef \
  --target @spam_bot \
  --reason spam \
  --count 10
```

### Burst Mode - Multiple Reasons
```bash
python burst_blocker.py \
  --api_id 12345 \
  --api_hash abcdef \
  --target @fake_account \
  --user_mode Burst \
  --reason fake,spam,violence \
  --count 3
```

### Full Mode - All Reasons
```bash
python burst_blocker.py \
  --api_id 12345 \
  --api_hash abcdef \
  --target +1234567890 \
  --user_mode Full \
  --count 1
```

### With Tor IP Rotation
```bash
python burst_blocker.py \
  --api_id 12345 \
  --api_hash abcdef \
  --target @attacker \
  --reason copyright \
  --count 20 \
  --use_tor \
  --interval 30
```

### Test Mode
```bash
python burst_blocker.py \
  --api_id 12345 \
  --api_hash abcdef \
  --target @test_user \
  --reason spam \
  --test
```

---

## 🎯 Available Report Reasons

| Key | Full Name | Description |
|-----|-----------|-------------|
| `child_abuse` | Child Abuse | Child exploitation, endangering minors |
| `copyright` | Copyright | Copyright infringement, pirated content |
| `fake` | Fake Account | Impersonation, fake identity |
| `geo` | Geo-Irrelevant | Location-irrelevant content |
| `drugs` | Illegal Drugs | Drug trafficking, substance abuse |
| `other` | Other | Miscellaneous violations |
| `personal` | Personal Details | Private info, doxxing |
| `porn` | Pornography | Adult content, obscene material |
| `spam` | Spam | Unsolicited messages, scams |
| `violence` | Violence | Threats, harassment, hate speech |

---

## 🌐 Tor Integration

### Setting Up Tor

1. **Install Tor:**
   ```bash
   # Ubuntu/Debian
   sudo apt install tor

   # macOS
   brew install tor

   # Windows
   # Download from https://www.torproject.org/
   ```

2. **Configure Tor Control Port:**
   
   Edit `/etc/tor/torrc` (or `torrc` without path):
   ```
   ControlPort 9051
   CookieAuthentication 1
   # OR for password auth:
   # HashedControlPassword (your_hashed_password)
   ```

3. **Start Tor:**
   ```bash
   sudo systemctl start tor
   # or
   tor
   ```

4. **Test connection:**
   ```bash
   python burst_blocker.py --api_id 12345 --api_hash abcdef --target @test --reason spam --use_tor --test
   ```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Burst Blocker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Why MIT License?**
- ✅ Permissive - allows commercial use
- ✅ Flexible - modification and distribution allowed  
- ✅ Simple - short and understandable
- ✅ Compatible - works with all dependencies
- ✅ Community - most popular open-source license

---

## ⚠️ Disclaimer

```
THIS SOFTWARE IS PROVIDED FOR EDUCATIONAL PURPOSES ONLY

By using this software, you agree to the following:

1. **Legitimate Use Only**: This tool is designed exclusively for reporting
   actual spam, harassment, and policy violations on Telegram.

2. **Account Responsibility**: Your Telegram account may be limited or banned
   if you misuse this tool. You alone are responsible for your account.

3. **Rate Limiting**: Respect Telegram's rate limits. Excessive reporting may
   result in temporary or permanent account restrictions.

4. **No Warranty**: This software is provided "AS IS" without warranty of any
   kind. The authors are not responsible for any consequences of its use.

5. **Compliance**: You must comply with Telegram's Terms of Service and
   all applicable laws and regulations.

6. **Ethical Use**: Do not use this tool for harassment, false reporting,
   or any unethical purposes.
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


---

## 📞 Support

- **Issues**: GitHub Issues
- **Telegram**: [@username](https://t.me/username)
- **Email**: support@example.com

---

<p align="center">
  Made with ❤️ for a cleaner Telegram
  <br>
  <sub>Fight spam, not users</sub>
</p>

---

This README features:
- **Clean, modern design** with emoji indicators
- **Structured sections** with table of contents
- **Visual elements** like badges and tables
- **Clear examples** for all use cases
- **Professional disclaimer** and legal information
- **MIT License** recommendation (most suitable for this type of tool)
- **Mobile-friendly** formatting

The MIT License is recommended because:
1. It's permissive and widely used
2. Allows both personal and commercial use
3. Simple and legally sound
4. Compatible with all dependencies (Telethon, Requests, etc.)
5. No "viral" requirements (unlike GPL)
