import utils_toolbox

def main(args) -> None:
    linphone1 = f"{args.test_dir}.Linphone1"
    client = utils_toolbox.DockerClient()
    client.list_containers()
    client.exec_in_container(linphone1, f'linphonecsh status register')
    client.wait_packet(args.interface, [{"step": "REGISTER"}, {"step": 401}, {"step": "REGISTER"}, {"step": 200}], timeout=75)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog='steps')
    parser.add_argument('-i', '--interface', default='test-network', help='interface to capture packet, default: test-network', type=str)
    parser.add_argument('-s', '--sipproxy_ip', help='ip of sipproxy', required=True, type=str)
    parser.add_argument('-t', '--test_dir', help='test dir name', required=True, type=str)
    arg = parser.parse_args()
    main(arg)