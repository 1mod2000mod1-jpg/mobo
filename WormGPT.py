try:
    from bs4 import BeautifulSoup
except ImportError:
    import os
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup
    import telebot,requests,re,html,tempfile,os;from bs4 import BeautifulSoup;from urllib.parse import urljoin   
love=telebot.TeleBot("8253064655:AAExNIiYf09aqEsW42A-rTFQDG-P4skucx4") # Token bot Telegram
WormGPT="http://sii3.moayman.top/DARK/api/wormgpt.php?text=hello" # API WormGPT
def ask_ai(text): 
    try: return requests.post(WormGPT,data={"text":text}).json().get("response","Error")
    except: return "Error"
def markdown_to_html(text):
    text=html.escape(text)
    text=re.sub(r'```(.*?)```',r'<pre>\1</pre>',text,flags=re.DOTALL)
    text=re.sub(r'`(.*?)`',r'<code>\1</code>',text)
    text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'\*(.*?)\*',r'<i>\1</i>',text)
    text=re.sub(r'__(.*?)__',r'<u>\1</u>',text)
    return text
def darkai():
    love.polling()
def extract_image(url):
    try:
        if any(url.lower().endswith(ext) for ext in [".jpg",".jpeg",".png",".webp"]): return url
        headers={"User-Agent":"Mozilla/5.0"}
        resp=requests.get(url,headers=headers)
        if resp.status_code!=200: return None
        soup=BeautifulSoup(resp.text,"html.parser")
        for tag in ["og:image","twitter:image"]:
            img=soup.find("meta",property=tag)
            if img and img.get("content"): return img["content"]
        img_tag=soup.find("img")
        if img_tag and img_tag.get("src"): return urljoin(url,img_tag["src"])
    except: return None
def extract_code_blocks(text): return re.findall(r'```(.*?)```',text,flags=re.DOTALL)
def get_file_extension(code_snippet):
    first_line=code_snippet.strip().splitlines()[0].lower()
    if "python" in first_line: return ".py"
    if "javascript" in first_line or "js" in first_line: return ".js"
    if "java" in first_line: return ".java"
    if "c++" in first_line or "cpp" in first_line: return ".cpp"
    if "c#" in first_line or "csharp" in first_line: return ".cs"
    if "php" in first_line: return ".php"
    if "html" in first_line: return ".html"
    return ".txt"
def ask_for_filename(code_snippet):
    try:
        prompt=f"Just give me a proper file name for this code without any extras:\n{code_snippet}"
        filename=requests.post(WormGPT,data={"text":prompt}).json().get("response","code_file")
        return re.sub(r'[^\w\- ]','',filename).strip()
    except: return "code_file"
@love.message_handler(commands=['start'])
def start_message(message):
    text="""<b>Hi im WormGPT 👋🏻</b>\n<b><blockquote>im an unfiltered artificial intelligence that can create any code you can think of</blockquote></b>\n<b><tg-spoiler><blockquote>The most powerful illegal artificial intelligence</blockquote></tg-spoiler></b>\n\n<b><u>im ready what do you want?</u></b>"""
    img_url=extract_image("https://pin.it/1HLRK6sTC") # link image /start
    if img_url: love.send_photo(message.chat.id,photo=img_url,caption=text,parse_mode="HTML",has_spoiler=True)
    else: love.send_message(message.chat.id,text,parse_mode="HTML")
@love.message_handler(func=lambda m:True)
def chat(message):
    reply=ask_ai(message.text)
    if len(reply)>4000:
        codes=extract_code_blocks(reply)
        if codes:
            code_snippet=codes[0]
            filename=ask_for_filename(code_snippet)+get_file_extension(code_snippet)
            temp_path=os.path.join(tempfile.gettempdir(),filename)
            with open(temp_path,"w",encoding="utf-8") as f: f.write(code_snippet)
            caption=(reply.replace(f"```{code_snippet}```","")[:1000]+"...") if len(reply)>1024 else reply.replace(f"```{code_snippet}```","")
            love.send_document(message.chat.id,open(temp_path,"rb"),caption=caption or " ")
            os.remove(temp_path)
            return
    love.send_message(message.chat.id,markdown_to_html(reply),parse_mode="HTML")
darkai()
