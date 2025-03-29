from curses.ascii import isblank
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import json
import subprocess
import re
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def IsIDValid(id:str):
    if id == "":
        return False
    elif id.isspace():
        return False
    elif bool(set(id) & {"/","?",".","\\","@","#","$","&","(",")","|",":","*",";","<",">","\""}):
        return False
    else:
        return True
    
def MD5Mapping(token:str):
    UIDsum = set()
    for file in os.listdir(f"superiorcache/{token}"):
        match = re.match(r'^(.*?)\.svg', file)
        if match:
            temp_superiorcacheid = match.group(1)       
            UIDsum.add(f"{token}nTRBPG{temp_superiorcacheid}")

    md5_to_text = {}
    for text in UIDsum:
        # 计算哈希并统一转为小写存储
        hash_key = hashlib.md5(text.encode('utf-8')).hexdigest().lower()
        md5_to_text[hash_key] = text
    return md5_to_text

@app.get("/")
async def main(token:str = "",superiorcacheid:str = "",twicecompile:bool = False,latex:str = "\\LaTeX",border:float = 0):

    if not os.path.exists("superiorcache"):
        os.mkdir("superiorcache")

    # 检查用户是否注册，并记录使用量
    with open("user.json","r") as file:
        userjson = json.load(file)

    allusertoken = list(userjson.keys())

    if not token in allusertoken:
        return {"error": "Unauthorised"}
    
    if int(userjson[token]["maxusage"]) != -1 and int(userjson[token]["currentusage"]) > int(userjson[token]["maxusage"]):
        return {"error": "InsufficientUsage"}

    # 为superior用户调用superiorcache
    if userjson[token]["superior"] == True and IsIDValid(superiorcacheid):
        if os.path.exists("superiorcache/" + token + "/" + superiorcacheid + ".svg"):
            return FileResponse("superiorcache/" + token + "/" + superiorcacheid + ".svg", media_type="image/svg+xml")
        
    userjson[token]["currentusage"] += 1

    with open("user.json","w") as file:
        json.dump(userjson,file,indent=4)

    # 创建一个临时工作文件夹
    current_folder = "cache/" + str(time.time())
    os.mkdir(current_folder)

    # 处理用户的latex、添加最小工作示例、保存到input.tex
    latexinput = "\\documentclass[10pt]{standalone}\n\\usepackage{amsmath}\n\\usepackage{amsthm}\n\\usepackage{amsfonts}\n\\usepackage{amssymb}\n\\usepackage{amstext}\n\\usepackage{tikz}\n\\usepackage{chemfig}\n\\usepackage[UTF8]{ctex}\n\\usepackage[version=4]{mhchem}\n\\usetikzlibrary{intersections,calc,backgrounds,knots}\n\\standaloneconfig{border=" + str(border) + "}\n\\begin{document}\n\n" + latex + "\n\n\\end{document}"

    os.system("touch " + current_folder + "/latexinput.tex")

    with open(current_folder + "/latexinput.tex", "w") as file:
        file.write(latexinput)

    # 调用xelatex进行编译得到pdf
    os.chdir(current_folder)
    try:
        # 调用xelatex命令，捕获标准输出和错误输出
        subprocess.run(
            ['xelatex', '-interaction=nonstopmode', "latexinput.tex"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将标准错误合并到标准输出
            check=True,                # 如果返回码非零则抛出异常
            text=True                  # 以文本形式返回输出内容
        )
    except subprocess.CalledProcessError as e:
        # 捕获子进程错误，包含返回码和输出内容
        os.chdir("..")
        os.chdir("..")
        matches = re.findall(r'\n(!.*?)\n', e.stdout)
        
        error_details = {
        "error": "LaTeXCompileFault",
        "returncode": e.returncode,
        "detail": "\n".join(matches)
        }
        return error_details
    # 二次编译（如果需要）
    if twicecompile == True:
        try:
            # 调用xelatex命令，捕获标准输出和错误输出
            subprocess.run(
                ['xelatex', '-interaction=nonstopmode', "latexinput.tex"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将标准错误合并到标准输出
                check=True,                # 如果返回码非零则抛出异常
                text=True                  # 以文本形式返回输出内容
            )
        except subprocess.CalledProcessError as e:
            # 捕获子进程错误，包含返回码和输出内容
            os.chdir("..")
            os.chdir("..")
            matches = re.findall(r'\n(!.*?)\n', e.stdout)
        
            error_details = {
            "error": "LaTeXCompileFault",
            "returncode": e.returncode,
            "detail": "\n".join(matches)
            }
            return error_details
    os.chdir("..")
    os.chdir("..")
    

    # 调用pdf2svg
    os.system("pdf2svg " + current_folder + "/latexinput.pdf" + " " + current_folder + "/latexoutput.svg")

    # 为superior用户创建superiorcache
    if userjson[token]["superior"] == True and IsIDValid(superiorcacheid):
        if not os.path.exists("superiorcache/" + token):
            os.mkdir("superiorcache/" + token)
        os.system("cp " + current_folder + "/latexoutput.svg" + " " + "superiorcache/" + token + "/" + superiorcacheid + ".svg")

    # 输出svg
    output_path = current_folder + "/latexoutput.svg"
    if not os.path.isfile(output_path):
        return {"error": "File not found"}
    return FileResponse(output_path, media_type="image/svg+xml")

@app.get("/superiorcache")
async def modify_superior_cache(action:str = "", token:str = "", superiorcacheid:str = ""):
    #读取用户列表
    with open("user.json","r") as file:
        userjson = json.load(file)

    allusertoken = list(userjson.keys())

    # 检查用户是否注册
    if (not token in allusertoken) or userjson[token]["superior"] != True:
        return {"error": "Unauthorised"}

    # 检查action是否合法
    valid_action_list = ["list", "delete"]
    if not action in valid_action_list:
        return {"error": "InvalidAction"}
    
    # 检查并记录使用量
    if int(userjson[token]["maxusage"]) != -1 and int(userjson[token]["currentusage"]) > int(userjson[token]["maxusage"]):
        return {"error": "InsufficientUsage"}

    userjson[token]["currentusage"] += 1

    with open("user.json","w") as file:
        json.dump(userjson,file,indent=4)

    if action == "list":
        # 生成HTML内容
        html_content = """<html>
    <head>
        <title>SVG Files List</title>
        <style>
            @font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:100;src:local("JetBrains Mono Thin"),local("JetBrainsMono-Thin"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Thin.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:100;src:local("JetBrains Mono Thin Italic"),local("JetBrainsMono-ThinItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ThinItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:200;src:local("JetBrains Mono ExtraLight"),local("JetBrainsMono-ExtraLight"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraLight.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:200;src:local("JetBrains Mono ExtraLight Italic"),local("JetBrainsMono-ExtraLightItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraLightItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:300;src:local("JetBrains Mono Light"),local("JetBrainsMono-Light"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Light.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:300;src:local("JetBrains Mono Light Italic"),local("JetBrainsMono-LightItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-LightItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:400;src:local("JetBrains Mono Regular"),local("JetBrainsMono-Regular"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Regular.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:400;src:local("JetBrains Mono Italic"),local("JetBrainsMono-Italic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Italic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:500;src:local("JetBrains Mono Medium"),local("JetBrainsMono-Medium"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Medium.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:500;src:local("JetBrains Mono Medium Italic"),local("JetBrainsMono-MediumItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-MediumItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:700;src:local("JetBrains Mono Bold"),local("JetBrainsMono-Bold"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Bold.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:700;src:local("JetBrains Mono Bold Italic"),local("JetBrainsMono-BoldItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-BoldItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:800;src:local("JetBrains Mono ExtraBold"),local("JetBrainsMono-ExtraBold"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraBold.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:800;src:local("JetBrains Mono ExtraBold Italic"),local("JetBrainsMono-ExtraBoldItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraBoldItalic.woff2") format("woff2");font-display:swap}
            table {border-collapse: collapse; width: 100%;}
            th, td {border: 1px solid #ddd; padding: 8px; text-align: left;}
            tr:nth-child(even) {background-color: #f2f2f2;}
            img {max-width: 200px; max-height: 200px;}
            code, tt {
            padding: .2em .4em;
            margin: 0;
            font-size: 85%;
            background-color: #656c7633;
            white-space: break-spaces;
            border-radius: 6px;
            font-family: 'JetBrains Mono';
}
        </style>
    </head>"""
        html_content += f"""
    <body>
        <h2>SVG Files under <code>{token}</code></h2>
        <table>
            <tr><th>SuperiorCacheID</th><th>UID</th><th>Preview</th></tr>"""

    # 检查目录是否存在以及是否为空目录
        if (not os.path.exists("superiorcache/" + token)) or len(os.listdir("superiorcache/" + token)) == 0:
            html_content += "<tr><td colspan='3'>No SVG files found</td></tr>"
        else:
            UIDsum = MD5Mapping(token)
            if not os.path.exists(f"superiorcache/{token}/map.json"):
                os.system("touch " + f"superiorcache/{token}/map.json")
            with open(f"superiorcache/{token}/map.json","w") as file:
                json.dump(UIDsum,file,indent=4)

            for file in os.listdir(f"superiorcache/{token}"):
                match = re.match(r'^(.*?)\.svg', file)
                if match:
                    temp_superiorcacheid = match.group(1)
                    html_content += f"""
            <tr>
                <td>{temp_superiorcacheid}</td>
                <td><a href="/superiorcache/{hashlib.md5((token+"nTRBPG"+temp_superiorcacheid).encode('utf-8')).hexdigest().lower()}.svg">{hashlib.md5((token+"nTRBPG"+temp_superiorcacheid).encode('utf-8')).hexdigest().lower()}</a></td>
                <td><img src="/?token={token}&superiorcacheid={temp_superiorcacheid}"></td>
            </tr>"""
        html_content += """</table></body></html>"""

        return Response(content=html_content, media_type="text/html")
    elif action == "delete":
        # 判断请求的文件是否存在
        if os.path.exists(f"superiorcache/{token}/{superiorcacheid}.svg"):
            try:
                os.remove(f"superiorcache/{token}/{superiorcacheid}.svg")
                error_details = {"success": "FileDeleted " + superiorcacheid + ".svg"}
                return error_details
            except Exception as e:
                return {"error": "DeletionFailed"}
        else:
            return {"error": "FileNotFound"}

@app.get("/superiorcache/{UID_svg}")
async def get_superior_cache(UID_svg:str):
    match = re.match(r'^(.*?)\.svg', UID_svg)
    if match:
        UID = match.group(1)
    else:
        return {"error": "InvalidUID"}

    for temp_token in os.listdir("superiorcache"):
        if os.path.exists(f"superiorcache/{temp_token}/map.json"):
            with open(f"superiorcache/{temp_token}/map.json","r") as file:
                loadedmap = json.load(file)
            tokenSid = loadedmap.get(UID.lower()) # token + 盐 + superiorcacheid
            if tokenSid != None:
                break
    if tokenSid == None:
        return {"error": "InvalidUID"}
    token, salt, superiorcacheid = tokenSid.partition("nTRBPG")
    if salt != "nTRBPG":
        return {"error": "InvalidUID"}
    if not os.path.exists(f"superiorcache/{token}/{superiorcacheid}.svg"):
        return {"error": "File not found"}
    return FileResponse(f"superiorcache/{token}/{superiorcacheid}.svg", media_type="image/svg+xml")

# 启动 FastAPI 应用程序
if __name__ == "__main__":
    os.system("rm -rf cache/")
    os.system("mkdir cache")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)