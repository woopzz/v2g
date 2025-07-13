import logging
import tempfile
from subprocess import Popen

import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO)

app = FastAPI()
last_gif_content = None

def yield_last_gif_content():
    yield last_gif_content

@app.post('/')
async def convert_video(file: UploadFile):
    with tempfile.NamedTemporaryFile('wb') as file_input:
        file_input.write(await file.read())

        # We have to specify the .gif suffix so ffmpeg understands the format of the output file.
        with tempfile.NamedTemporaryFile('rb', suffix='.gif') as file_output:
            # We use -y to automatically agree on file replacement.
            popen = Popen(['ffmpeg', '-y', '-i', file_input.name, file_output.name])
            code = popen.wait()
            if code != 0:
                logging.error(f'Could convert a video file to a gif file. ffmpeg exit code: {code}')
                return {'ok': False}

            global last_gif_content
            last_gif_content = file_output.read()

    return {'ok': True}

@app.get('/')
def get_gif():
    if last_gif_content:
        return StreamingResponse(yield_last_gif_content(), media_type='image/gif')
    else:
        return HTTPException(status_code=404)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
