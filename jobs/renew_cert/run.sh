#! /bin/bash -e

RENEW_BEFORE_DAYS=${RENEW_BEFORE_DAYS}
EMAIL=${EMAIL}
ARCHIVE_FILE_PASS=${ARCHIVE_FILE_PASS}
JIANGUOYUN_USER=${JIANGUOYUN_USER}
JIANGUOYUN_KEY=${JIANGUOYUN_KEY}
JIANGUOYUN_URI=${JIANGUOYUN_URI}
export DOMAIN=${DOMAIN}
export TIMEOUT=${TIMEOUT:-10}
export DP_Id=${DP_Id}
export DP_Key=${DP_Key}

CERT_EXPIRE_DATE=`curl --connect-timeout $TIMEOUT -I -s -v https://www.$DOMAIN/ 2>&1 | grep 'expire date:' | cut -d" " -f 5-`

echo "$DOMAIN certificate expire at $CERT_EXPIRE_DATE"

export FORCE_RENEW_CERT=1 

if [ $FORCE_RENEW_CERT ] || [ `date +%s` -ge `date -d "$CERT_EXPIRE_DATE $RENEW_BEFORE_DAYS days ago" +%s` ]; then
  # install acme.sh
  git clone https://github.com/acmesh-official/acme.sh.git
  (cd acme.sh && ./acme.sh --install --accountemail $EMAIL)
  export ACME_INSTALL_DIR=~/.acme.sh

  # renew cert files
  $ACME_INSTALL_DIR/acme.sh --register-account -m $EMAIL --set-default-ca --server zerossl
  $ACME_INSTALL_DIR/acme.sh --issue --dns dns_dp -d $DOMAIN -d "vpn.$DOMAIN" -d "*.$DOMAIN" -d "*.nas.$DOMAIN"

  # package cert files
  DIR=$DOMAIN.`date +%Y%m%d`
  mkdir -p $DIR
  $ACME_INSTALL_DIR/acme.sh --install-cert -d $DOMAIN --cert-file "$DIR/$DOMAIN.pem" --key-file "$DIR/$DOMAIN.key" --fullchain-file "$DIR/fullchain.cer" --reloadcmd "ls -l $PWD/$DIR"
  ARCHIVE_FILE=$DOMAIN.zip
  zip -rj -P $ARCHIVE_FILE_PASS $ARCHIVE_FILE $DIR

  # archive cert files
  curl --user "$JIANGUOYUN_USER:$JIANGUOYUN_KEY" -T $ARCHIVE_FILE ${JIANGUOYUN_URI}ssl/

  # push to servers
  scripts=`ls ./lib | sort`
  for script in $scripts; do
    ./lib/$script
  done
else
  echo 'Nothing to do.'
fi
