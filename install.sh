#!/bin/sh

#set -x
#set -e
set -u

echo "Installing myeasyserver..."

ASSET="myeasyserver.tgz"
REPOS="myeasyserver"
USER='stefapi'
PACKAGE_UPDATE="true"
NOSUDO="false"

ARCHITECTURE="$(uname -m)"
# Non pris en charge sur les systèmes 32 bits
case "$ARCHITECTURE" in
    "armv7" | "i686" | "i386")
    echo "myeasyserver is not supported on 32 bits systems"
    exit 1
    ;;
esac

if [ "$(command -v sudo | wc -l)" -eq 0 ]; then
    echo "sudo not found"
    alias sudo=""
    NOSUDO="true"
fi
if [ "$(id -run)" != "root" ] && [ "${NOSUDO}" = "true" ]; then
    echo "Please run as root"
    exit 1
fi


### --------------------------------
### CLI arguments
### --------------------------------
UPDATE="false"
VERSION="latest"
while [ -n "${1-}" ]; do
    case "$1" in
    --update) UPDATE="true" ;;
    --version)
        shift # Move to the next parameter
        VERSION="$1" # Assign the value to VERSION
        if [ -z "$VERSION" ]; then
            echo "Option --version requires a value" && exit 1
        fi
        ;;
    --)
        shift # The double dash makes them parameters
        break
        ;;
    *) echo "Option $1 not recognized" && exit 1 ;;
    esac
    shift
done


OS="$(cat /etc/[A-Za-z]*[_-][rv]e[lr]* | grep "^ID=" | cut -d= -f2 | uniq | tr '[:upper:]' '[:lower:]' | tr -d '"' | grep -v vagrant)"
SUB_OS="$(cat /etc/[A-Za-z]*[_-][rv]e[lr]* | grep "^ID_LIKE=" | cut -d= -f2 | uniq | tr '[:upper:]' '[:lower:]' | tr -d '"' || echo 'unknown')"

  # Installs a generic dependency based on the operating system.
  #
  # @param dependency The name of the dependency to install.
  # @param os The name of the operating system.
  #
  # @return The exit code of the installation command.
generic_install() {
    local dependency="${1}"
    local os="${2}"
    if [ "${os}" = "debian" ]; then
          if [ "${PACKAGE_UPDATE}" = "true" ]; then
                sudo DEBIAN_FRONTEND=noninteractive apt-get update
                PACKAGE_UPDATE="false"
          fi
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${dependency}"
      return $?
    elif [ "${os}" = "ubuntu" ] || [ "${os}" = "pop" ]; then
          if [ "${PACKAGE_UPDATE}" = "true" ]; then
                sudo DEBIAN_FRONTEND=noninteractive apt-get update
                PACKAGE_UPDATE="false"
          fi
          sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${dependency}"
          return $?
    elif [ "${os}" = "centos" ] || [ "${os}" = "rocky" ] || [ "${os}" = "almalinux" ]; then
          if [ "${PACKAGE_UPDATE}" = "true" ]; then
              sudo DEBIAN_FRONTEND=noninteractive apt-get update
              sudo yum -y update
              PACKAGE_UPDATE="false"
          fi
         sudo yum install -y --allowerasing "${dependency}"
         return $?
    elif [ "${os}" = "fedora" ]; then
          if [ "${PACKAGE_UPDATE}" = "true" ]; then
                sudo dnf -y check-update
                PACKAGE_UPDATE="false"
          fi
          sudo dnf -y install "${dependency}"
          return $?
    elif [ "${os}" = "alpine" ]; then
          if [ "${PACKAGE_UPDATE}" = "true" ]; then
                sudo apk update
                PACKAGE_UPDATE="false"
          fi
          sudo apk add "${dependency}"
          return $?
    elif [ "${os}" = "arch" ]; then
          if [ "${PACKAGE_UPDATE}" = "true" ]; then
                sudo pacman -Syu --noconfirm "${dependency}"
                PACKAGE_UPDATE="false"
          fi
          if ! sudo pacman -Sy --noconfirm "${dependency}" ; then
                if command -v yay > /dev/null 2>&1 ; then
                      sudo -u $SUDO_USER yay -Sy --noconfirm "${dependency}"
                else
                      echo "Could not install \"${dependency}\", either using pacman or the yay AUR helper. Please try installing it manually."
                      return 1
                fi
          fi
          return $?
    else
          return 1
    fi
}

  # Function to check if a dependency is installed, and if not, attempt to install it.
  #
  # @param dependency the name of the dependency to check.
  # @param packages The name of the packages to install.
  #
  # @return The exit code of the installation command.
check_dependency_and_install() {
  local dependency="${1}"
  shift

  if ! command -v "${dependency}" >/dev/null; then
    echo "Installing ${dependency}"

    INSTALL_FAIL="true"
    for package in "${@}"; do
        generic_install "${package}" "${OS}"
        install_result=$?

        if [ $install_result -eq 0 ]; then
          echo "${dependency} installed"
          INSTALL_FAIL="false"
          break
        fi
    done
    if [ $INSTALL_FAIL = "true" ]; then
      echo "Your system ${OS} is not supported trying with sub_os ${SUB_OS}"
      for package in "${@}"; do
        generic_install "${dependency}" "${SUB_OS}"
        install_sub_result=$?

        if [ $install_sub_result -eq 0 ]; then
          echo "${dependency} installed"
          INSTALL_FAIL="false"
          break
        fi
      done
    fi
    if [ $INSTALL_FAIL = "true" ]; then
      echo "Your system ${SUB_OS} is not supported please install ${dependency} manually"
      exit 1
    fi
  fi
}

# function to configure a service based on the operating system
#
# @param service_name the name of the service to configure
# @param service the name of the service to configure
#
# @return The exit code of the installation command.
install_service() {
  local service_name="${1}"
  local service="${2}"
  local parameters="${3}"
  local parameters_daemon="${4}"

  if [ "${OS}" = "debian" ] || [ "${OS}" = "ubuntu" ] || [ "${OS}" = "pop" ] || [ "${OS}" = "centos" ] || [ "${OS}" = "rocky" ] || [ "${OS}" = "almalinux" ] || [ "${OS}" = "fedora" ] || [ "${OS}" = "arch" ]; then
    echo "[Unit]
Description=${service_name}
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=${service} ${parameters}

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/"${service_name}".service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable "${service_name}"
    sudo systemctl stop "${service_name}"
    sudo systemctl start "${service_name}"
  elif [ "${OS}" = "alpine" ]; then
    echo "#! /sbin/openrc-run

name=\"${service_name}\"
command=\"${service}\"
command_args=\"${parameters_daemon}\"

depend() {
  need net
  use dns
}

start_pre() {
    checkpath --directory /var/run/${service_name}
}" | sudo tee /etc/init.d/"${service_name}" >/dev/null
    sudo chmod +x /etc/init.d/"${service_name}"
    sudo rc-update add "${service_name}" default
    sudo rc-service "${service_name}" stop
    sudo rc-service "${service_name}" start
  fi
}

check_dependency_and_install "curl" "curl"
check_dependency_and_install "python" "python3"
check_dependency_and_install "pip" "python3-pip" "py3-pip"

TEST_ENV="false"
if [ -d /vagrant ] && [ -f /vagrant/requirements.txt ]; then
    cd /vagrant
    TEST_ENV="true"
else

# If version was not given it will install the latest version
    if [ "${VERSION}" = "latest" ]; then
      LATEST_VERSION=$(curl -s https://api.github.com/repos/$USER/$REPOS/releases/latest | grep tag_name | cut -d '"' -f4)
      VERSION="${LATEST_VERSION}"
    fi

    URL="https://github.com/$USER/$REPOS/releases/download/$VERSION/$ASSET"

    if [ "${UPDATE}" = "false" ]; then
        exit
    elif [ "${CUR_VERSION}" = "${VERSION}" ]; then
        sudo bash -c "
        mkdir -p /usr/local/share/$REPOS
        cd /usr/local/share/$REPOS
        curl --location \"$URL\" -o $REPOS.tgz
        tar xfz $REPOS.tgz
        "
        cd /usr/local/share/$REPOS
    fi
fi

# Install dependencies and install package
sudo pip install -e . --break-system-packages

TEST_EV="false"
# Install service and Start it
if [ "${TEST_EV}" = "true" ]; then
    myeasyserver --port 8080 serve
else
    sudo adduser --system --no-create-home myeasyserver
    sudo addgroup --system myeasyserver
    sudo mkdir -p /etc/myeasyserver
    sudo myeasyserver -W /etc/myeasyserver/config.toml -S /run/myeasyserver/myeasyserver.sock serve
    install_service "myeasyserver" "myeasyserver" "serve" "serve --daemon"

    # Install docker. Beware, this will do nothing if this script is run in a docker container
    myeasyserver --socket /run/myeasyserver/myeasyserver.sock cli install_docker
fi


