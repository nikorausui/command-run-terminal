import subprocess
import threading
import os
import pty
from datetime import datetime
import re

class ShellLogger:
    def __init__(self, log_file="log.txt"):
        self.log_file = log_file
        self.ignore_patterns = [
            r"┌──\(kali㉿kali\)-\[.*?\]",
            r"└─\$",
            r"stty: .*",
            r"^\s*$",
            r"\[.*?\] exec:.*"
        ]
        
    def clean_ansi(self, text):
        # ANSIエスケープシーケンスを除去
        ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 非キャプチャグループ
                [@-Z\\-_]
                |\[
                [0-?]*  # パラメータバイト
                [ -/]*  # 中間バイト
                [@-~]   # 最終バイト
            )
        ''', re.VERBOSE)
        
        # 特殊な制御文字も除去
        text = re.sub(r'\x1B\][0-9;]*;*[a-zA-Z]', '', text)
        text = re.sub(r'\x1B\[[\?0-9;]*[a-zA-Z]', '', text)
        text = re.sub(r'\x1B\[[\?0-9;]*[mK]', '', text)
        text = ansi_escape.sub('', text)
        
        # その他の制御文字を除去
        text = re.sub(r'\x0f|\x1B\[H|\x1B\[2J|\x1B\[K|\r', '', text)
        return text
        
    def should_ignore(self, message):
        cleaned_message = self.clean_ansi(message)
        return any(re.search(pattern, cleaned_message) for pattern in self.ignore_patterns)
        
    def log(self, message, message_type="INFO"):
        if self.should_ignore(message):
            return
            
        # メッセージをクリーンアップ
        cleaned_message = self.clean_ansi(message).strip()
        if not cleaned_message:  # クリーニング後が空の場合はスキップ
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{cleaned_message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    def log_command(self, command):
        if not self.should_ignore(command):
            self.log(f"Command: {command}", "CMD")
        
    def log_output(self, output):
        if not self.should_ignore(output):
            self.log(f"{output}", "OUT")
        
    def log_error(self, error):
        if not self.should_ignore(error):
            self.log(f"{error}", "ERR")

def create_pty_process():
    master, slave = pty.openpty()
    process = subprocess.Popen(
        ["bash"],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        preexec_fn=os.setsid,
        universal_newlines=True
    )
    return process, master, slave

def read_output(master_fd, logger):
    buffer = ""
    while True:
        try:
            data = os.read(master_fd, 1024).decode()
            if data:
                print(data, end='', flush=True)
                buffer += data
                
                if '\n' in buffer:
                    lines = buffer.split('\n')
                    for line in lines[:-1]:
                        if line.strip():
                            logger.log_output(line.strip())
                    buffer = lines[-1]
                    
        except OSError:
            break
        except UnicodeDecodeError:
            # デコードエラーの場合はスキップ
            buffer = ""
            continue

def main():
    logger = ShellLogger()
    
    try:
        process, master, slave = create_pty_process()
        output_thread = threading.Thread(
            target=read_output, 
            args=(master, logger), 
            daemon=True
        )
        output_thread.start()

        while True:
            try:
                user_input = input()
                if user_input.strip().lower() == 'exitt':
                    logger.log("")
                    break
                    
                if user_input.strip():
                    logger.log_command(user_input)
                os.write(master, (user_input + '\n').encode())
                
            except EOFError:
                logger.log("EOF received")
                break
            except Exception as e:
                logger.log_error(str(e))

    except Exception as e:
        logger.log_error(f"Critical error: {str(e)}")
        
    finally:
        process.terminate()
        os.close(master)
        os.close(slave)
        print("\nBash shell terminated.")

if __name__ == "__main__":
    main()
