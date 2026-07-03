![python](https://img.shields.io/pypi/pyversions/gubbi.svg)
![license](https://img.shields.io/github/license/prahladyeri/gubbi.svg)
[![paypal](https://img.shields.io/badge/PayPal-blue.svg?logo=paypal)](https://paypal.me/prahladyeri)
[![follow](https://img.shields.io/twitter/follow/prahladyeri.svg?style=social)](https://x.com/prahladyeri)

# gubbi

*Minimalist LLM chatbot 🐤*

# Installation

	pip install gubbi
	
# Configuration

All configuration is stored in `~/.config/gubbi/settings.json`. At least one provider needs added in order for chat to work. Either add it manually or program will ask for inputs on the first start.

```json
{
    "providers": {
        "github": {
            "slug": "github",
            "url": "https://models.github.ai/inference",
            "default_model_id": "openai/gpt-4.1-mini"
        }
    }
}
```
	
# Usage

	gubbi -a # add provider/model
	gubbi -c # chat
	
# Commands

```plaintext
	#help => List commands
	#exit => Quit chat
	#use <provider> => Switch provider
	#model <model_name> => Switch model
	#attach <path> => Attach a file
	#clear => Clear context
	#save => Save current chat
	#load <filename> => Load an earlier chat
	#models <filename> => List all models
	#providers <filename> => List all providers	
```

# Screenshot

![gubbi-chatbot](assets/screenshot.png)