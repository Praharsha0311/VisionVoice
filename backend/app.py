from flask import Flask, Response
from flask_cors import CORS
import main
import navigation

app = Flask(__name__)
CORS(app)

@app.route('/video/child_safety')
def video_feed_child_safety():
    return Response(main.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video/navigation')
def video_feed_navigation():
    return Response(navigation.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
