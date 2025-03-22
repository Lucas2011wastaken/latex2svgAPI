from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import json
import subprocess
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main(token:str = "null",superiorcacheid:str = "null",twicecompile:bool = False,latex:str = "\\LaTeX",border:float = 0):

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
        
    userjson[token]["currentusage"] += 1

    # 为superior用户调用superiorcache
    if userjson[token]["superior"] == True and superiorcacheid != "null":
        if os.path.exists("superiorcache/" + token + "/" + superiorcacheid + ".svg"):
            return FileResponse("superiorcache/" + token + "/" + superiorcacheid + ".svg", media_type="image/svg+xml")

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
    if userjson[token]["superior"] == True and superiorcacheid != "null":
        if not os.path.exists("superiorcache/" + token):
            os.mkdir("superiorcache/" + token)
        os.system("cp " + current_folder + "/latexoutput.svg" + " " + "superiorcache/" + token + "/" + superiorcacheid + ".svg")

    # 输出svg
    output_path = current_folder + "/latexoutput.svg"
    if not os.path.isfile(output_path):
        return {"error": "File not found"}
    return FileResponse(output_path, media_type="image/svg+xml")

@app.get("/superiorcache")
async def get_superior_cache(action:str = "null", token:str = "null", superiorcacheid:str = "null"):
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
}
        </style>
    </head>"""
        html_content += f"""
    <body>
        <h2>SVG Files under <code>{token}</code></h2>
        <table>
            <tr><th>SuperiorCacheID</th><th>Preview</th></tr>"""

    # 检查目录是否存在以及是否为空目录
        if (not os.path.exists("superiorcache/" + token)) or len(os.listdir("superiorcache/" + token)) == 0:
            html_content += "<tr><td colspan='2'>No SVG files found</td></tr>"
        else:
            for file in os.listdir(f"superiorcache/{token}"):
                match = re.match(r'^(.*?)\.svg', file)
                if match:
                    temp_superiorcacheid = match.group(1)
                    html_content += f"""
            <tr>
                <td>{temp_superiorcacheid}</td>
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

# 启动 FastAPI 应用程序
if __name__ == "__main__":
    os.system("rm -rf cache/")
    os.system("mkdir cache")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)