from flask import Flask, request, send_file, jsonify, Response, after_this_request
from utils import download_audio, cut_audio, TMP_DIR, get_video_info
import os, uuid, json, threading

app = Flask(__name__)

tasks = {}

@app.route('/say',  methods=['GET'])
def say():
    return jsonify({"message": "This app is success."}) 

@app.route('/get-duration', methods=['POST'])
def get_duration_route():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        video_info = get_video_info(url)
        duration_seconds = video_info.get('duration')
        title = video_info.get("title", "No Title")
        url = video_info.get("webpage_url", url)
        # 秒→HH:MM:SS形式に変換
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        formatted = f"{hours:02}:{minutes:02}:{seconds:02}"

        response_data = {
                "url": url,
                "title": title,
                "start": "00:00:00",
                "end": formatted
            }

        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type='application/json'
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            content_type='application/json'
        ), 500

def process_cut(task_id, url, start, end):
    output_filename = task_id + ".mp3"
    final_output_path = os.path.join(TMP_DIR, output_filename)
    try:
        downloaded_path = download_audio(url)
        cut_audio(downloaded_path, final_output_path, start, end)
        tasks[task_id] = {"status": "done", "path": final_output_path}
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}
    finally:
        if os.path.exists(downloaded_path):
            os.remove(downloaded_path)

@app.route("/cut", methods=["POST"])
def api_cut():
    data = request.get_json()
    url = data.get("url")
    start = data.get("start")
    end = data.get("end")

    if not all([url, start, end]):
        return jsonify({"error": "Missing required parameters"}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}

    thread = threading.Thread(target=process_cut, args=(task_id, url, start, end))
    thread.start()

    return jsonify({"task_id": task_id}), 202


@app.route("/cut-result/<task_id>", methods=["GET"])
def get_cut_result(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Invalid task ID"}), 404

    if task["status"] == "processing":
        return jsonify({"status": "processing"}), 202

    elif task["status"] == "error":
        return jsonify({"status": "error", "error": task["error"]}), 500

    elif task["status"] == "done":
        file_path = task["path"]

        @after_this_request
        def remove_from_tmp(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🧹 削除しました: {file_path}")
            except Exception as e:
                print(f"❌ ファイル削除失敗: {e}")
            return response

        return send_file(file_path, as_attachment=True)
