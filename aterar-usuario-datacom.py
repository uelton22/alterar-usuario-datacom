from pyzabbix import ZabbixAPI
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Configurações do servidor Zabbix
zabbix_server = "http://192.168.1.1/zabbix/api_jsonrpc.php"
zabbix_username = "user"
zabbix_password = "pwd"

# Conexão com o Zabbix
zapi = ZabbixAPI(zabbix_server)
zapi.login(zabbix_username, zabbix_password)

# Função para executar comandos via SSH
def execute_ssh_commands(device_config, commands):
    try:
        with ConnectHandler(**device_config) as net_connect:
            output = ""
            for command in commands:
                output += net_connect.send_command_timing(command + "\n")
            return True, output
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        return False, str(e)

# Comandos para equipamentos Datacom e Huawei
datacom_commands = [
    "config",
    "no aaa user",
    "aaa user admin",
    "password $1$jMi7XzraYR1wXB/f.HZL.Wk/g/",
    "group admin",
    "commit",
    "exit"
]

# Comandos para equipamentos Huawei (se necessário)
huawei_commands = [
    # Adicione os comandos específicos para Huawei aqui
]

# Obter lista de hosts do Zabbix
hosts = zapi.host.get(
    output=["hostid", "name"],
    selectInterfaces=["ip"],
    selectTags="extend",
    evaltype=0,
    #tag cadastrado no zabbix
    tags=[{
        "tag": "mapa",
        "value": "diagrama",
        "operator": 0
    }]
)

# Lista para armazenar hosts de sucesso
successful_hosts = []
success = False
output = "Tipo de equipamento não suportado ou não encontrado."

# Processar cada host
for host in hosts:
    ip_address = host['interfaces'][0]['ip']
    # Obter a descrição do sistema do host
    item = zapi.item.get(hostids=host['hostid'], search={"key_": "system.descr[sysDescr.0]"})
    if not item:
        continue
    last_value = item[0]['lastvalue']
    #tipo de equipamento coletado no zabbix
    if "DmOS" in last_value:
        # Configuração para equipamento Datacom
        device_config = {
            'device_type': 'cisco_ios',  # Verifique o tipo de dispositivo correto
            'host': ip_address,
            'username': 'user',
            'password': 'pwd'
        }
        print(f"Conectando ao Datacom {ip_address}")
        success, output = execute_ssh_commands(device_config, datacom_commands)
    # elif "Huawei" in last_value:
    #     # Configuração para equipamento Huawei
    #     device_config = {
    #         'device_type': 'huawei',  # Verifique o tipo de dispositivo correto
    #         'host': ip_address,
    #         'username': 'user',
    #         'password': 'pwd'
    #     }
        print(f"Conectando ao Huawei {ip_address}")
        success, output = execute_ssh_commands(device_config, huawei_commands)

    if success:
        print(f"Comandos executados com sucesso em {ip_address}")
        successful_hosts.append(ip_address)
    else:
        print(f"Falha ao executar comandos em {ip_address}: {output}")

# Salvar IPs de sucesso em um arquivo
with open('successful_hosts.txt', 'w') as file:
    for ip in successful_hosts:
        file.write(ip + "\n")

print("Execução concluída. Hosts de sucesso salvos em 'successful_hosts.txt'")

