import os
import re
import io
from PIL import Image
from pydub import AudioSegment
import telebot
import face_recognition
import config


# Creation of a folder for contact data.
path = "Contact data"
os.makedirs(path, exist_ok=True)

# Connection of the API
bot = telebot.TeleBot(config.API_TOKEN)

# Welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Welcome! I'm the bot that saves your audio messages by user ID and stores images containing faces. Don't hesitate to send yours!")


@bot.message_handler(content_types=['voice'])
def voice_message(message):
    '''Saves audio messages by user ID and changing frame rate and name of them'''

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Saves the audio message locally
    contact_path = file_saver(message, file_info, downloaded_file)

    # Converts the file to .wav with the correct enumeration
    convert_wav16khz(contact_path)

@bot.message_handler(content_types=['photo'])
def image_message(message):
    '''Function to save images containing faces'''

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # With the next code instead of saving the image localy it gets it directly from memory and after decides if save it or not.
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    image = face_recognition.load_image_file(image_stream)
    face_locations = face_recognition.face_locations(image)

    # Checks if there is any location. In case there is one or more, it saves the image.
    if face_locations:
        # Saves the image locally
        file_saver(message, file_info, downloaded_file)



def convert_wav16khz(contact_path):
    '''Function to change frame rate and name of the file'''


    def extract_number(filename):
        '''Function to get the number of files with the format audio_message_n.wav'''
        match = re.search(r'audio_message_(\d+)\.wav', filename)
        if match:
            return int(match.group(1))
        else:
            return -1


    # 'files' is a list of files in the folder
    files = os.listdir(contact_path)
    
    # 'existing_wav_files' is a list of numbers from files with the format audio_message_n.wav
    existing_wav_files = [f for f in files if re.match(r'audio_message_\d+\.wav', f)]
    # 'highest_num' is the highest number in the existing_wav_files
    highest_num = max([extract_number(f) for f in existing_wav_files], default=-1)
    
    # The created file ended in .oga is converted to .wav with the correct enumeration
    file_name = next((f for f in files if f.endswith('.oga')), None)
    file_path = os.path.join(contact_path, file_name)
    if os.path.isfile(file_path):
        new_voice = f'audio_message_{highest_num + 1}.wav'
        new_voice_path = os.path.join(contact_path, new_voice)
        voice = AudioSegment.from_file(file_path).set_frame_rate(16000)
        voice.export(new_voice_path, format='wav')
        os.remove(file_path)

def file_saver(message, file_info, downloaded_file):
    '''
    Creates a new folder for the user if it doesn't exist and saves the initial file in the folder.
    Returns the path of the folder where the file is saved.
    '''
    contact_id = str(message.from_user.id)
    contact_path = os.path.join(path, contact_id)
    contactPathExists = os.path.exists(contact_path)
    if not contactPathExists:
        os.mkdir(contact_path)

    base_name = os.path.basename(file_info.file_path)
    open_path = os.path.join(contact_path, base_name)
    with open(open_path, 'wb') as new_voice:
        new_voice.write(downloaded_file)

    return contact_path

bot.polling(none_stop=True)