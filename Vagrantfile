VAGRANTFILE_API_VERSION = "2"

NODES = [
  { name: "node1", ip: "192.168.80.139", cpus: 2, memory: 2048 },
  { name: "node2", ip: "192.168.80.140", cpus: 2, memory: 2048 },
]

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "bento/ubuntu-20.04"
  config.vm.box_check_update = false

  config.vm.provider "vmware_desktop" do |vmware|
    vmware.gui = false
    vmware.linked_clone = false
  end

  NODES.each do |node|
    config.vm.define node[:name] do |machine|

      machine.vm.hostname = node[:name]
      machine.vm.network "private_network", ip: node[:ip]

      machine.vm.provider "vmware_desktop" do |vmware|
        vmware.cpus   = node[:cpus]
        vmware.memory = node[:memory]
        vmware.vmx["displayName"] = "ansible-lab-#{node[:name]}"
      end

      machine.vm.provision "shell", inline: <<-SHELL
        set -e
        apt-get update -qq
        apt-get install -y -qq python3 python3-pip openssh-server
        id deploy &>/dev/null || useradd -m -s /bin/bash deploy
        echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy
      SHELL

    end
  end

end
