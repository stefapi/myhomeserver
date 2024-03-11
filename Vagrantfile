Vagrant.configure("2") do |config|
  config.vm.define "homeserverdebug", autostart: false do |subvm|
    autostart = false
    subvm.disksize.size = '60GB'
    subvm.vm.box = "debian/bookworm64"
    subvm.vm.hostname = "homeserverdebug"
    subvm.vm.network "public_network", type: "dhcp"
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
      # define dedicated configuration for debugging
      # warning: never use in production, the configuration is really unsecured
      #subvm.vm.provision "shell", inline: <<-SHELL
      #   groupadd docker
      #   useradd dockerdebug -p '$y$j9T$mymCpCZTgedvmNYzhHiWQ0$BQdQOExE8fy4d2m9cDrdt4Lhxjo1/MF1oMCt3rcecWD'
      #   sed -Ei 's/^#?\s*PasswordAuthentication\s+(yes|no)/PasswordAuthentication yes/' /etc/ssh/sshd_config
      #   usermod -aG docker dockerdebug
      #   service ssh restart
      #SHELL
  end
  config.vm.define "homeserverdebian", autostart: false do |subvm|
    autostart = false
    subvm.disksize.size = '60GB'
    subvm.vm.box = "debian/bookworm64"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8081
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.define "homeserverubuntu", autostart: false do |subvm|
    subvm.disksize.size = '60GB'
    subvm.vm.box = "ubuntu/lunar64"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8082
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.define "homeserverfedora", autostart: false do |subvm|
    subvm.disksize.size = '60GB'
    subvm.vm.box = "bento/fedora-38"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8083
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.define "homeservercentos", primary: true do |subvm|
    subvm.disksize.size = '60GB'
    subvm.vm.box = "bento/centos-stream-9"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8084
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.define "homeserverarch", autostart: false do |subvm|
    subvm.disksize.size = '60GB'
    subvm.vm.box = "archlinux/archlinux"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8085
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.define "homeserveralma", autostart: false do |subvm|
    subvm.disksize.size = '60GB'
    subvm.vm.box = "bento/almalinux-9"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8086
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.define "homeserverrocky", autostart: false do |subvm|
    subvm.disksize.size = '60GB'
    subvm.vm.box = "bento/rockylinux-9"
    subvm.vm.hostname = "homeserver"
    #subvm.vm.network "private_network", type: "dhcp"
    subvm.vm.network "forwarded_port", guest: 80, host: 8087
    subvm.vm.provider "virtualbox" do |vb|
        #   # Display the VirtualBox GUI when booting the machine
        #   vb.gui = true
        #   vb.memory = "16384"
      end
  end

  config.vm.provision "shell", inline: <<-SHELL
      # bash /vagrant/install.sh
  SHELL

end
