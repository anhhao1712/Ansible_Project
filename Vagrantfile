Vagrant.configure("2") do |config|
  config.vm.define "node1" do |node1|
    node1.vm.box = "bento/ubuntu-20.04"
    node1.vm.network "private_network", ip: "192.168.56.10"
    node1.vm.provider "vmware_desktop" do |v|
      v.gui = false 
      v.memory = 1024
    end
  end

  config.vm.define "node2" do |node2|
    node2.vm.box = "bento/ubuntu-20.04"
    node2.vm.network "private_network", ip: "192.168.56.11"
    node2.vm.provider "vmware_desktop" do |v|
      v.gui = false
      v.memory = 1024
    end
  end
end