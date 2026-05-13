from flask import Flask, render_template, request, redirect, session
import sqlite3
import unicodedata
import re

def remove_accents(text):
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'đ', 'd', text).replace('Đ', 'D').lower()

from flask import Flask, request, jsonify, render_template_string
import sqlite3 
app = Flask(__name__)
app.secret_key = "123456"
DB_NAME = "civil.db"  
# WHITELIST KẾT HÔN 
MARRIAGE_FIELDS = {
    "ho_ten_vo": "Họ tên vợ",
    "ngay_sinh_vo": "Ngày sinh vợ",
    "dan_toc_vo": "Dân tộc vợ",
    "quoc_tich_vo": "Quốc tịch vợ",
    "noi_cu_tru_vo": "Nơi cư trú vợ",
    "giay_to_vo": "Giấy tờ vợ",
    "ho_ten_chong": "Họ tên chồng",
    "ngay_sinh_chong": "Ngày sinh chồng",
    "dan_toc_chong": "Dân tộc chồng",
    "quoc_tich_chong": "Quốc tịch chồng",
    "noi_cu_tru_chong": "Nơi cư trú chồng",
    "giay_to_chong": "Giấy tờ chồng",
    "noi_dang_ky_ket_hon": "Nơi đăng ký",
} 
# WHITELIST KHAI SINH 
BIRTH_FIELDS = {
    "ho_ten": "Họ tên",
    "gioi_tinh": "Giới tính",
    "ngay_sinh": "Ngày sinh",
    "noi_sinh": "Nơi sinh",
    "dan_toc": "Dân tộc",
    "quoc_tich": "Quốc tịch",
    "ho_ten_cha": "Họ tên cha",
    "nam_sinh_cha": "Năm sinh cha",
    "ho_ten_me": "Họ tên mẹ",
    "nam_sinh_me": "Năm sinh mẹ",
    "noi_cu_tru": "Nơi cư trú",
} 
# HELPERS 
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn 
INDEX_HTML = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Tra cứu giấy tờ</title>
  <style>
    body{
      font-family: Arial, sans-serif;
      background:#f4f6f9;
      padding:20px;
    }
    .card{
      max-width:1000px;
      margin:auto;
      background:white;
      padding:20px;
      border-radius:10px;
      box-shadow:0 4px 12px rgba(0,0,0,0.1);
    }
    h2{
      text-align:center;
      margin-bottom:10px;
    }
.controls{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin-bottom:15px;
  align-items:center;
}
    select,input{
  padding:8px 10px;
  font-size:14px;
  border-radius:6px;
  border:1px solid #ccc;
}

button{
  padding:8px 10px;
  font-size:14px;
  border-radius:6px;
  border:none;
  background:#007bff;
  color:white;
  cursor:pointer;
}


#q{
  width:200px;
}
    button{
      background:#007bff;
      color:white;
      border:none;
      cursor:pointer;
    }
    button:hover{
      background:#0056b3;
    }
    table{
      width:100%;
      border-collapse:collapse;
      margin-top:15px;
      font-size:13px;
    }
    th,td{
      border:1px solid #ddd;
      padding:8px;
      text-align:left;
    }
    th{
      background:#e9f0ff;
    }
    .no-result{
      text-align:center;
      color:#666;
      padding:15px;
    }
 #suggestions{
  position:absolute;
  top:100%;
  left:0;
  width:100%;
  background:white;
  border:1px solid #ccc;
  border-top:none;
  z-index:1000;
  max-height:200px;
  overflow-y:auto;
}

#suggestions div{
  padding:6px;
  cursor:pointer;
}

#suggestions div:hover{
  background:#f0f0f0;
}
   </style>
</head>
<body> 
<div class="card"> 
<h2>TRA CỨU GIẤY TỜ HÀNH CHÍNH</h2>
<p><b>Database:</b> {{ dbname }}</p> 
<div class="controls">
  <select id="doc">
    <option value="marriage">Giấy kết hôn</option>
    <option value="birth">Giấy khai sinh</option>
  </select> 
  <select id="field"></select> 
<div style="position:relative; width:200px;">
  <input id="q" style="width:100%;">
  <div id="suggestions"></div>
</div>
<div style="margin-left:auto; display:flex; gap:10px;">
  <button onclick="search()">Tìm</button>
  <button onclick="getAll()">Tất cả</button>
</div>
</div> 
<div id="result" class="no-result">Chưa có dữ liệu</div> 
</div> 
<script>
const marriageFields = {{ marriage | safe }};
const birthFields = {{ birth | safe }}; 
const docSelect = document.getElementById("doc");
const fieldSelect = document.getElementById("field"); 
function loadFields(){
  fieldSelect.innerHTML = "";
  const fields = docSelect.value === "marriage" ? marriageFields : birthFields;
  for(const k in fields){
    const opt = document.createElement("option");
    opt.value = k;
    opt.innerText = fields[k];
    fieldSelect.appendChild(opt);
  }
}
loadFields();
docSelect.onchange = loadFields; 
async function search(){
  const type = docSelect.value;
  const field = fieldSelect.value;
  const q = document.getElementById("q").value;
  const r = await fetch(`/search?type=${type}&field=${field}&q=${q}`);
  const text = await r.text();
  render(text);
} 
async function getAll(){
  const type = docSelect.value;
  const r = await fetch(`/all?type=${type}`);
  const text = await r.text();
  render(text);
} 
function render(text){
  if(!text.trim()){
    document.getElementById("result").innerHTML =
      "<div class='no-result'>Không có kết quả</div>";
    return;
  } 
  const rows = text.trim().split("\\n").map(x => JSON.parse(
    x.replace(/'/g,'"')
     .replace("None","null")
  )); 
  let html = "<table><tr>";
  Object.keys(rows[0]).forEach(k => html += `<th>${k}</th>`);
  html += "</tr>"; 
  rows.forEach(r=>{
    html += "<tr>";
    Object.values(r).forEach(v=>{
      html += `<td>${v ?? ""}</td>`;
    });
    html += "</tr>";
  }); 
  html += "</table>";
  document.getElementById("result").innerHTML = html;
}
const input = document.getElementById("q");
const suggestionBox = document.getElementById("suggestions");

input.addEventListener("input", async () => {
  const q = input.value;
  if(!q){
    suggestionBox.innerHTML = "";
    return;
  }

  const type = docSelect.value;
  const field = fieldSelect.value;

  const r = await fetch(`/suggest?type=${type}&field=${field}&q=${q}`);
  const data = await r.json();

  let html = "";
  data.forEach(item=>{
    html += `<div onclick="selectSuggest('${item}')"
              style="padding:5px;cursor:pointer;">
              ${item}
            </div>`;
  });

  suggestionBox.innerHTML = html;
});

function selectSuggest(val){
  input.value = val;
  suggestionBox.innerHTML = "";
}
</script> 
</body>
</html>
""" 
@app.route("/")
def index():

    if "user" not in session:
        return redirect("/login")

    return render_template_string(
        INDEX_HTML,
        dbname=DB_NAME,
        marriage=MARRIAGE_FIELDS,
        birth=BIRTH_FIELDS
    )

# API ALL 
@app.route("/all")
def api_all():
    doc_type = request.args.get("type")
    table = "marriage" if doc_type == "marriage" else "birth" 
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 200")
    rows = cur.fetchall()
    conn.close() 
    return "\n".join([str(dict(r)) for r in rows]) 
# API SEARCH 
@app.route("/search")
def api_search():
    doc_type = request.args.get("type")
    field = request.args.get("field")
    q = request.args.get("q", "")

    fields = MARRIAGE_FIELDS if doc_type == "marriage" else BIRTH_FIELDS
    table = "marriage" if doc_type == "marriage" else "birth"

    if field not in fields:
        return "Sai cột dữ liệu"

    conn = get_db()
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    conn.close()

    q_norm = remove_accents(q)

    result = []
    for r in rows:
        val = remove_accents(r[field])
        if q_norm in val:
            result.append(dict(r))

    return "\n".join([str(r) for r in result])
@app.route("/suggest")
def suggest():
    doc_type = request.args.get("type")
    field = request.args.get("field")
    q = request.args.get("q", "")

    fields = MARRIAGE_FIELDS if doc_type == "marriage" else BIRTH_FIELDS
    table = "marriage" if doc_type == "marriage" else "birth"

    if field not in fields:
        return jsonify([])

    conn = get_db()
    cur = conn.cursor()

    cur.execute(f"SELECT DISTINCT {field} FROM {table}")
    rows = cur.fetchall()
    conn.close()

    q_norm = remove_accents(q)

    suggestions = []
    for r in rows:
        val = r[field]
        if val and q_norm in remove_accents(val):
            suggestions.append(val)

    return jsonify(suggestions[:10])

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("civil.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/")

        else:
            return render_template(
                "login.html",
                error="Sai tài khoản hoặc mật khẩu"
            )

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")

# RUN 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
