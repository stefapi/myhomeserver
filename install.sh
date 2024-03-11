#!/usr/bin/env bash
set -x
set -o errexit
set -o nounset
set -o pipefail

echo "Installing myeasyserver..."

ASSET="myeasyserver.tgz"
REPOS="myeasyserver"
USER='stefapi'
PACKAGE_UPDATE="true"

ARCHITECTURE="$(uname -m)"
# Not supported on 32 bits systems
if [[ "$ARCHITECTURE" == "armv7"* ]] || [[ "$ARCHITECTURE" == "i686" ]] || [[ "$ARCHITECTURE" == "i386" ]]; then
    echo "fastapi_vite_vue is not supported on 32 bits systems"
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

function generic_install() {
  local dependency="${1}"
  local os="${2}"

  if [[ "${os}" == "debian" ]]; then
    if [[ ${PACKAGE_UPDATE} == "true" ]]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get update
        PACKAGE_UPDATE="false"
    fi
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${dependency}"
    return 0
  elif [[ "${os}" == "ubuntu" || "${os}" == "pop" ]]; then
    if [[ ${PACKAGE_UPDATE} == "true" ]]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get update
        PACKAGE_UPDATE="false"
    fi
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${dependency}"
    return 0
  elif [[ "${os}" == "centos" || "${os}" == "rocky" || "${os}" == "almalinux" ]]; then
    if [[ ${PACKAGE_UPDATE} == "true" ]]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get update
        sudo yum -y update
        PACKAGE_UPDATE="false"
    fi
    sudo yum install -y --allowerasing "${dependency}"
    return 0
  elif [[ "${os}" == "fedora" ]]; then
    if [[ ${PACKAGE_UPDATE} == "true" ]]; then
        sudo dnf -y check-update
        PACKAGE_UPDATE="false"
    fi
    sudo dnf -y install "${dependency}"
    return 0
  elif [[ "${os}" == "arch" ]]; then
    if [[ ${PACKAGE_UPDATE} == "true" ]]; then
        sudo pacman -Syu  --noconfirm "${dependency}"
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
    return 0
  else
    return 1
  fi
}

function check_dependency_and_install() {
  local dependency="${1}"

  if ! command -v "${dependency}" >/dev/null; then
    echo "Installing ${dependency}"
    generic_install "${dependency}" "${OS}"
    install_result=$?

    if [[ install_result -eq 0 ]]; then
      echo "${dependency} installed"
    else
      echo "Your system ${OS} is not supported trying with sub_os ${SUB_OS}"
      generic_install "${dependency}" "${SUB_OS}"
      install_sub_result=$?

      if [[ install_sub_result -eq 0 ]]; then
        echo "${dependency} installed"
      else
        echo "Your system ${SUB_OS} is not supported please install ${dependency} manually"
        exit 1
      fi
    fi
  fi
}

check_dependency_and_install "curl"
check_dependency_and_install "python3"
check_dependency_and_install "python3-pip"

if  [[ -d /vagrant && -f /vagrant/requirements.txt ]]; then
    cd /vagrant
else

# If version was not given it will install the latest version
    if [[ "${VERSION}" == "latest" ]]; then
      LATEST_VERSION=$(curl -s https://api.github.com/repos/$USER/$REPOS/releases/latest | grep tag_name | cut -d '"' -f4)
      VERSION="${LATEST_VERSION}"
    fi

    URL="https://github.com/$USER/$REPOS/releases/download/$VERSION/$ASSET"

    if [[ "${UPDATE}" == "false" ]]; then
        exit
    elif [[ "${CUR_VERSION}" == "${VERSION}" ]]; then
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

