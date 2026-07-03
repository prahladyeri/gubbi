##
# cli.py
#
# @author Prahlad Yeri <prahladyeri@yahoo.com>
# @license MIT
import os, sys
import json
import argparse
import subprocess
import keyring
from openai import OpenAI
from utils import cfghelper
from gubbi import __version__, PKG_NAME
from urllib.parse import urljoin


CONFIG_DIR = cfghelper.get_config_dir(PKG_NAME)
cfg = None
provider_slug = None # current provider
model_id = None # current model
repl_prompt = ""

COMMANDS = {
    "use": cmd_use,
    "attach": cmd_attach,
    "model": cmd_model,
    "provider": cmd_provider,
}

def add_model(provider_slug):
    prov = cfg['providers'][provider_slug]
    client = OpenAI(
        api_key=keyring.get_password(PKG_NAME, f"{provider_slug}_apikey"),
        base_url = prov['url'],
    )
    try:
        models = list(client.models.list())
    except Exception as e:
        print(f"Unable to fetch models: {e}")
        return False
    if not models:
        print("Provider returned no models.")
        return False
    for idx, model in enumerate(models):
        print(f"[{idx+1}]. {model.id}")
    idx = input("Choose a default model:")
    if not idx.isdigit():
        print("Please enter a number")
        return False
        
    idx = int(idx) - 1
    if idx < 0 or idx >= len(models): 
        print("Invalid selection")
        return False
    prov['default_model_id'] = models[idx].id
    cfghelper.save_settings(PKG_NAME, cfg)
    print(f"Default model set to '{models[idx].id}'.")
    return True
    

def add_provider():
    slug = input("Enter provider short name, e.g. 'groq':")
    url = input("Enter provider base url:")
    api_key = input("Add provider api key:")
    if slug and url and api_key:
        keyring.set_password(PKG_NAME, f"{slug}_apikey", api_key)
        if not 'providers' not in cfg.keys(): cfg['providers'] = {}
        provider = {'slug': slug, 'url': url, 'default_model_id': None}
        cfg['providers'][slug] = provider
        cfghelper.save_settings(PKG_NAME, cfg)
        add_model(slug)
        return True # Provider added, proceed now
    else:
        return False
        
def dispatch_command(cmd):
    global provider_slug, model_id
    action = cmd.split(' ')
    if action == '#use' 
        pass # switch provider
    elif action == '#model'
        pass # switch model
    elif action == '#help'
        pass # print help text
    else 
        pass # invalid command
        
def chat():
    global repl_prompt
    provider_slug = cfg['providers'][0].slug
    model_id = cfg['providers'][0]['default_model_id']
    repl_prompt = f"{provider_slug}/{model_id}> "
    stack = [{
        "role": "system",
        "content": "Converse in terminal text, no markdown unless specifically asked for. Use the <file name='/foo/bar.txt'></file> at the end of message for sending/receiving text files"
    }] # @todo: save this to a log or something to retrieve later
    while True: # repl
        text = input(repl_prompt)
        if text.startswith("#"):
            dispatch_command(text)
            continue
        else: # continue regular chat
            stack.append({'role': 'user', 'content': text})
            client = OpenAI(
                api_key=keyring.get_password(PKG_NAME, f"{provider_slug}_apikey"),
                base_url = cfg.providers[provider_slug]['url'],
            )
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=stack
                )
            except Exception as ex:
                print(response.choices[0].message.content)
                print("Error:", ex)
                continue
            msg = response.choices[0].message.content
            print(msg)
            stack.append({'role': 'assistant', 'content': msg})
            
def main():
    global provider_slug, model_id, repl_prompt
    cfg = cfghelper.get_settings(f"{PKG_NAME}")
    parser = argparse.ArgumentParser(description='Gubbi chat interface')
    parser.add_argument('-c', '--chat', help='Start chat repl')
    parser.add_argument('-a', '--add-provider', help='Add OpenAI compatible provider', action='store_true', default=False)
    args = parser.parse_args()
    if args.add_provider:
        add_provider()
        return
    
    if 'providers' not in cfg:
        print("No OpenAI compatible provider found.")
        if not add_provider(): return
        
    if args.chat:
        chat()
        return
        
    print("Too few arguments")
    

if __name__ == '__main__':
    main()