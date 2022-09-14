import json
import os
from time import sleep
import zlib
import getpass
import pyotp
from jinja2 import Template

ascii_art = b'x\x9c\xb5S\xb1\x11\x04!\x08\xcc\xaf\n\x02s\x1ar\xe6\x1b\xb1\xf8\x17\x04\x04\x0e\xff/9"\xc4\x85uW\xbd' \
			b'\x00\x9b\x04ePE\xaekG\t>N)\xe2\x1a\xd0\xda\x87\x02)\xab ' \
			b'\xb9\xbe:\xe0!\xfa/\xb9oCS\xa5\x02\x05\x81\x11\xd7kt\x9e\x82\xbb\xf7\x8ee\xf2U\xe2\xb6A&\xb0*\x8c\x8e' \
			b'\xcc%z\xf2a\x18\x08\xd9\xb8\xaf\x8eX\xb1\x1d\xb3\xf2\xd9\x06N\x0b\x05B&\xd7\x1d%\xe9R\x8b\xab\x03v\x92f' \
			b'\xdb\xf7\xf9\xbaz\xc0\xc7sW\x1c\x07zwF \xbfg\xf9m%r\xd3\xdb\xcc\x82\x05\xee\x10p\xba\x03N\xcdF[= ' \
			b'<V\xc9\x97\xe74\x942\xd6\xcb\xe7\xd3d\xd5\xd9&\xc3\xc9\x8eC\x8b.\x0cS\x14\xb1\x9d\x94\xc92\xe9z\xfa' \
			b'-~\xc7\xf1\x83\xa1=\xb8"^&\xdf\x17\xf0&\xb9Y\x99b_@E\xfe\x05\xad&\xec\xfb '


def confirm():
	print("Enter y to continue, anything else to quit")
	if not input() in ["y", "Y", "yes"]:
		exit()


sleep(0.5)

print(zlib.decompress(ascii_art).decode('ascii'))

config_dict = {}

sleep(0.5)
print("Setting up an instance of Flask Deployer")
confirm()

print("\n")
print("Flask Deployer requires access to sudo to execute some of its commands")
print("As a result, this password needs to be stored in the config file")
confirm()
print("\n")
sudo_psw = getpass.getpass(prompt="Enter your sudo password")
config_dict["secrets"]["sudo_psw"] = sudo_psw
print("\n")

print("Getting install information...")
config_dict["secrets"]["projects_folder"] = os.getcwd() + "/flask-projects"
config_dict["secrets"]["deployer_location"] = os.getcwd()
config_dict["secrets"]["install_username"] = getpass.getuser()
sleep(0.5)
print("Done")

print("Setting up TOTP authentication")
print("Enter the following code into your TOTP app, ie Google Authenticator")
config_dict["secrets"]["totp_secret"] = pyotp.random_base32()
print(config_dict["secrets"]["totp_secret"])
totp = pyotp.TOTP(config_dict["secrets"]["totp_secret"])

print("\n")
print("Get ready to enter the generated code to confirm TOTP enrollment")
sleep(1)
print("Enter the generated code:")


if not totp.verify(input()):
	print("TOTP verification failed")
	exit()

print("TOTP verification successful")

print("Saving config data.")

with open("config.json", "w") as file:
	file.write(json.dumps(config_dict, indent=4))

# create service file
with open("config_templates/service", "r") as file:
	service = Template(file.read())

output = service.render(
	path=config_dict["secrets"]["deployer_location"],
	user="mattl1598",
	project_name="flask-deployer"
)

with open("/etc/systemd/system/flask-deployer2.service", "w") as file:
	file.write(output)

# create nginx file
with open("config_templates/nginx", "r") as file:
	nginx = Template(file.read())

print("Enter url for flask-deployer instance:")
url = input()

output = nginx.render(
	path=config_dict["secrets"]["deployer_location"],
	user="mattl1598",
	project_name="flask-deployer",
	url=url
)

with open("/etc/nginx/sites-available/flask-deployer", "w") as file:
	file.write(output)


# sudo nano /etc/nginx/sites-available/open-amdram-portal
# sudo nano /etc/systemd/system/open-amdram-portal.service
