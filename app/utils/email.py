import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

def _send_email_sync(message, email_to):
    if settings.MAIL_SSL_TLS:
        server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10)
    else:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10)
        if settings.MAIL_STARTTLS:
            server.starttls()

    if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

    server.sendmail(message["From"], email_to, message.as_string())
    server.quit()

async def send_otp_email(email_to: str, otp: str) -> bool:
    """
    Envia um e-mail premium com o código PIN de autenticação.
    """
    logger.info(f"A preparar envio de OTP para {email_to}")

    if not settings.MAIL_SERVER or not settings.MAIL_USERNAME:
        logger.warning("Configurações de e-mail ausentes no ficheiro .env. O e-mail não será enviado fisicamente, mas o OTP foi impresso no terminal.")
        return True

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Código de Acesso - Helpdesk"
        message["From"] = settings.MAIL_FROM or settings.MAIL_USERNAME
        message["To"] = email_to

        text_content = f"O seu código de acesso (PIN) para login é: {otp}. Válido por 10 minutos."
        html_content = f"""
        <html>
          <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 50px; margin-bottom: 50px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden;">
              <tr>
                <td align="center" style="background: linear-gradient(135deg, #1f4068, #162447); padding: 40px 0;">
                  <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 1px;">Helpdesk</h1>
                </td>
              </tr>
              <tr>
                <td style="padding: 40px 50px 30px 50px;">
                  <p style="font-size: 16px; line-height: 1.6; color: #333333; margin: 0 0 20px 0;">Olá,</p>
                  <p style="font-size: 16px; line-height: 1.6; color: #333333; margin: 0 0 30px 0;">Utilize o código de acesso temporário (PIN) abaixo para efetuar o seu login no portal:</p>
                  <table align="center" border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto 35px auto;">
                    <tr>
                      <td align="center" style="background-color: #f1f3f8; border-radius: 6px; padding: 15px 30px; letter-spacing: 5px; font-size: 32px; font-weight: 700; color: #1f4068; border: 1px dashed #cbd5e1;">
                        {otp}
                      </td>
                    </tr>
                  </table>
                  <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0 0 20px 0; text-align: center;">Este código é válido por <strong>10 minutos</strong>. Por questões de segurança, não o partilhe.</p>
                </td>
              </tr>
              <tr>
                <td style="background-color: #f8fafc; padding: 25px 50px; text-align: center; border-top: 1px solid #e2e8f0;">
                  <p style="font-size: 12px; color: #94a3b8; margin: 0;">&copy; {datetime.now().year} Helpdesk. Todos os direitos reservados.</p>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """

        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        await asyncio.to_thread(_send_email_sync, message, email_to)
        
        logger.info("E-mail de OTP enviado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail de OTP: {e}")
        return False
