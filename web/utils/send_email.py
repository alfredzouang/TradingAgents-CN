"""
通用邮件发送工具
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
import os

def send_email(subject, content, to_addr, smtp_host=None, smtp_port=None, username=None, password=None, use_ssl=True, attachment_path=None):
    """
    发送邮件（支持PDF附件）

    Args:
        subject: 邮件标题
        content: 邮件正文（支持HTML）
        to_addr: 收件人邮箱（字符串或列表）
        smtp_host: SMTP服务器地址（默认读取环境变量 SMTP_HOST）
        smtp_port: SMTP端口（默认465，或读取 SMTP_PORT）
        username: 登录用户名（默认读取 SMTP_USER）
        password: 登录密码（默认读取 SMTP_PASS）
        use_ssl: 是否使用SSL（默认True）
        attachment_path: 附件文件路径（如PDF），可选
    """
    smtp_host = smtp_host or os.getenv("SMTP_HOST")
    smtp_port = int(smtp_port or os.getenv("SMTP_PORT", 465))
    username = username or os.getenv("SMTP_USER")
    password = password or os.getenv("SMTP_PASS")
    from_addr = username

    print(f"[send_email] SMTP_HOST={smtp_host}, SMTP_PORT={smtp_port}, USER={username}, TO={to_addr}, SUBJECT={subject}")

    if not (smtp_host and smtp_port and username and password):
        print("[send_email] 缺少SMTP配置，终止发送")
        raise ValueError("SMTP配置不完整，请设置 SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS 环境变量")

    if isinstance(to_addr, str):
        to_addr = [to_addr]

    try:
        if attachment_path:
            msg = MIMEMultipart()
            msg.attach(MIMEText(content, "html", "utf-8"))
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
        else:
            msg = MIMEText(content, "html", "utf-8")

        msg["From"] = Header(from_addr, "utf-8")
        msg["To"] = Header(", ".join(to_addr), "utf-8")
        msg["Subject"] = Header(subject, "utf-8")

        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        server.login(username, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
        server.quit()
        print(f"[send_email] 邮件已发送到 {to_addr}")
    except Exception as e:
        print(f"[send_email] 发送失败: {e}")
        raise
