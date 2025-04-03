from fastapi import FastAPI, Response, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
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
        raise HTTPException(status_code=401, detail="Unauthorised")
    
    if int(userjson[token]["maxusage"]) != -1 and int(userjson[token]["currentusage"]) > int(userjson[token]["maxusage"]):
        raise HTTPException(status_code=403, detail="InsufficientUsage")

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
        return JSONResponse(
        status_code=400,
        content={
        "error": "LaTeXCompileFault",
        "returncode": e.returncode,
        "detail": "\n".join(matches)
        }
        )
    
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
            return JSONResponse(
            status_code=400,
            content={
            "error": "LaTeXCompileFault",
            "returncode": e.returncode,
            "detail": "\n".join(matches)
            }
        )
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
        raise HTTPException(status_code=404, detail="FileNotFound")
    return FileResponse(output_path, media_type="image/svg+xml")

@app.get("/superiorcache")
async def modify_superior_cache(action:str = "", token:str = "", superiorcacheid:str = ""):
    #读取用户列表
    with open("user.json","r") as file:
        userjson = json.load(file)

    allusertoken = list(userjson.keys())

    # 检查用户是否注册
    if (not token in allusertoken) or userjson[token]["superior"] != True:
        raise HTTPException(status_code=401, detail="Unauthorised")

    # 检查action是否合法
    valid_action_list = ["list", "delete"]
    if not action in valid_action_list:
        raise HTTPException(status_code=400, detail="InvalidAction")
    
    # 检查并记录使用量
    if int(userjson[token]["maxusage"]) != -1 and int(userjson[token]["currentusage"]) > int(userjson[token]["maxusage"]):
        raise HTTPException(status_code=403, detail="InsufficientUsage")

    userjson[token]["currentusage"] += 1

    with open("user.json","w") as file:
        json.dump(userjson,file,indent=4)

    if action == "list":
        # 生成HTML内容
        html_content = """<html>
    <head>
        <title>SVG Files List</title>
<style>
.result-box {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    background: #f8f9fa;
}

.live-results {
    max-height: 300px;
    overflow-y: auto;
    margin: 10px 0;
}

.result-item {
    padding: 8px;
    font-family: 'JetBrains Mono';
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.result-item.success {
    color: #2e7d32;
    background: #edf7ed;
}

.result-item.fail {
    color: #d32f2f;
    background: #fdecea;
}

.summary {
    padding: 12px;
    border-radius: 4px;
    margin-top: 15px;
}

.all-success {
    background: #e8f5e9;
    border: 1px solid #c8e6c9;
}

.has-fail {
    background: #ffebee;
    border: 1px solid #ffcdd2;
}

.progress {
    color: #666;
    margin-bottom: 10px;
    font-size: 0.9em;
}
        <style>
            @font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:100;src:local("JetBrains Mono Thin"),local("JetBrainsMono-Thin"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Thin.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:100;src:local("JetBrains Mono Thin Italic"),local("JetBrainsMono-ThinItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ThinItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:200;src:local("JetBrains Mono ExtraLight"),local("JetBrainsMono-ExtraLight"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraLight.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:200;src:local("JetBrains Mono ExtraLight Italic"),local("JetBrainsMono-ExtraLightItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraLightItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:300;src:local("JetBrains Mono Light"),local("JetBrainsMono-Light"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Light.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:300;src:local("JetBrains Mono Light Italic"),local("JetBrainsMono-LightItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-LightItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:400;src:local("JetBrains Mono Regular"),local("JetBrainsMono-Regular"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Regular.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:400;src:local("JetBrains Mono Italic"),local("JetBrainsMono-Italic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Italic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:500;src:local("JetBrains Mono Medium"),local("JetBrainsMono-Medium"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Medium.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:500;src:local("JetBrains Mono Medium Italic"),local("JetBrainsMono-MediumItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-MediumItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:700;src:local("JetBrains Mono Bold"),local("JetBrainsMono-Bold"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-Bold.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:700;src:local("JetBrains Mono Bold Italic"),local("JetBrainsMono-BoldItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-BoldItalic.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:800;src:local("JetBrains Mono ExtraBold"),local("JetBrainsMono-ExtraBold"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraBold.woff2") format("woff2");font-display:swap}@font-face{font-family:'JetBrains Mono';font-style:italic;font-weight:800;src:local("JetBrains Mono ExtraBold Italic"),local("JetBrainsMono-ExtraBoldItalic"),url("//cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/fonts/webfonts/JetBrainsMono-ExtraBoldItalic.woff2") format("woff2");font-display:swap}
            table {border-collapse: collapse; width: 100%;}
            th:first-child, td:first-child {
                width: 30px;
                text-align: center;
            }
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
            .action-bar {
                margin: 15px 0;
                text-align: right;
            }
        </style>
    </head>"""
        html_content += f"""
    <body>
        <h2>SVG Files under <code>{token}</code></h2>
        <form>
            <div class="action-bar">
                <input type="text" id="searchInput" placeholder="regex filter...">
                <label style="margin-left:15px;margin-right:15px">
                <input type="checkbox" id="SelectAll"> SelectAll
                </label>
                <button type="submit">Delete</button>
            </div>
        <table>
            <tr><th>Select</th><th>SuperiorCacheID</th><th>UID</th><th>Preview</th></tr>"""

    # 检查目录是否存在以及是否为空目录
        if (not os.path.exists("superiorcache/" + token)) or len(os.listdir("superiorcache/" + token)) == 0:
            html_content += "<tr><td colspan='4'>No SVG files found</td></tr>"
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
                <td><input type="checkbox" name="selected_ids[]" value="{temp_superiorcacheid}"></td>
                <td>{temp_superiorcacheid}</td>
                <td><a href="/superiorcache/{hashlib.md5((token+"nTRBPG"+temp_superiorcacheid).encode('utf-8')).hexdigest().lower()}.svg">{hashlib.md5((token+"nTRBPG"+temp_superiorcacheid).encode('utf-8')).hexdigest().lower()}</a></td>
                <td><img src="/?token={token}&superiorcacheid={temp_superiorcacheid}"></td>
            </tr>"""
        html_content += """<script>
document.querySelector('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // 从当前页面URL获取参数
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    // 参数校验
    if (!token) {
        alert('token获取失败，请重新进入页面');
        return;
    }

    // 获取选中的ID列表
    const selected = Array.from(document.querySelectorAll('input[name="selected_ids[]"]:checked'))
        .map(checkbox => checkbox.value);

    if (selected.length === 0) {
        alert('请至少选择一项');
        return;
    }

    if (!confirm(`确定要删除选中的 ${selected.length} 个项目吗？`)) return;

    // 创建结果容器
    const resultDiv = document.createElement('div');
    resultDiv.id = 'delete-results';
    resultDiv.style.margin = '15px 0';
    document.querySelector('.action-bar').after(resultDiv);

    // 显示加载状态
    resultDiv.innerHTML = `
        <div class="result-box">
            <div class="progress">Processing... <span id="progress">0/${selected.length}</span></div>
            <div id="live-results" class="live-results"></div>
        </div>
    `;

    const liveResults = document.getElementById('live-results');
    const progressSpan = document.getElementById('progress');

    // 存储所有请求结果
    const results = [];

    // 逐个发送删除请求
    for (const [index, cacheId] of selected.entries()) {
        const requestUrl = `/superiorcache?token=${token}&action=delete&superiorcacheid=${encodeURIComponent(cacheId)}`;
        
        try {
            const startTime = Date.now();
            const response = await fetch(requestUrl);
            const result = await response.json();
            
            const success = response.ok && result.success;
            const duration = Date.now() - startTime;
            
            results.push({
                cacheId,
                success,
                duration,
                message: result.success || result.error
            });

            // 实时显示结果
            liveResults.innerHTML += `
                <div class="result-item ${success ? 'success' : 'fail'}">
                    <code>${cacheId}</code>
                    <span title="${result.success || result.error}">${success ? '✓' : '✗'} <code>(${duration}ms)</code></span>
                </div>
            `;

            // 删除成功则移除行
            if (success) {
                document.querySelector(`input[value="${cacheId}"]`).closest('tr').style.opacity = '0.5';
                setTimeout(() => {
                    document.querySelector(`input[value="${cacheId}"]`).closest('tr').remove();
                }, 500);
            }
        } catch (error) {
            results.push({
                cacheId,
                success: false,
                message: `网络异常：${error.message}`
            });
            liveResults.innerHTML += `
                <div class="result-item fail">
                    <code>${cacheId}</code>
                    <span>✗ ${result.success || result.error || error.message}请求失败</span>
                </div>
            `;
        }
        // 更新进度
        progressSpan.textContent = `${index + 1}/${selected.length}`;
        liveResults.scrollTop = liveResults.scrollHeight;
    }

    // 显示最终统计
    const successCount = results.filter(r => r.success).length;
    resultDiv.innerHTML += `
        <div class="summary ${successCount === selected.length ? 'all-success' : 'has-fail'}">
            ${selected.length} task(s) done, ${successCount} success, ${selected.length - successCount} failure.
        </div>
    `;
});

// 全选功能
document.getElementById('SelectAll').addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('input[name="selected_ids[]"]');
    checkboxes.forEach(checkbox => checkbox.checked = this.checked);
});
// 获取搜索框元素并监听输入事件
document.getElementById('searchInput').addEventListener('input', function(e) {
  const searchTerm = e.target.value.trim();
  if (!searchTerm) return;
  const regex = new RegExp(searchTerm, 'i'); // 创建不区分大小写的正则表达式

  // 获取所有目标复选框
  const checkboxes = document.querySelectorAll('input[name="selected_ids[]"]');
  checkboxes.forEach(checkbox => {
    // 获取关联的文本
    const rowText = checkbox.closest('tr').textContent; // 假设复选框在表格行中

    // 执行正则匹配
    if (regex.test(rowText)) {
      checkbox.checked = true; // 匹配则选中
    } else {
      checkbox.checked = false; // 不匹配则取消选中
    }
  });
});
</script></table></form></body></html>"""

        return Response(content=html_content, media_type="text/html")
    elif action == "delete":
        # 判断请求的文件是否存在
        if not IsIDValid(superiorcacheid):
            raise HTTPException(status_code=400, detail="InvalidUID")
        if os.path.exists(f"superiorcache/{token}/{superiorcacheid}.svg"):
            try:
                os.remove(f"superiorcache/{token}/{superiorcacheid}.svg")
                error_details = {"success": "FileDeleted " + superiorcacheid + ".svg"}
                return error_details
            except Exception as e:
                raise HTTPException(status_code=500, detail="DeletionFailed")
        else:
            raise HTTPException(status_code=404, detail="FileNotFound")

@app.get("/superiorcache/{UID_svg}")
async def get_superior_cache(UID_svg:str):
    match = re.match(r'^(.*?)\.svg', UID_svg)
    if match:
        UID = match.group(1)
    else:
        raise HTTPException(status_code=400, detail="InvalidUID")


    for temp_token in os.listdir("superiorcache"):
        if os.path.exists(f"superiorcache/{temp_token}/map.json"):
            with open(f"superiorcache/{temp_token}/map.json","r") as file:
                loadedmap = json.load(file)
            tokenSid = loadedmap.get(UID.lower()) # token + 盐 + superiorcacheid
            if tokenSid != None:
                break
    if tokenSid == None:
        raise HTTPException(status_code=400, detail="InvalidUID")

    token, salt, superiorcacheid = tokenSid.partition("nTRBPG")
    if salt != "nTRBPG":
        raise HTTPException(status_code=400, detail="InvalidUID")

    if not os.path.exists(f"superiorcache/{token}/{superiorcacheid}.svg"):
        raise HTTPException(status_code=404, detail="FileNotFound")
    return FileResponse(f"superiorcache/{token}/{superiorcacheid}.svg", media_type="image/svg+xml")

# 启动 FastAPI 应用程序
if __name__ == "__main__":
    os.system("rm -rf cache/")
    os.system("mkdir cache")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )