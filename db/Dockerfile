FROM postgres:15-alpine

# Custom pg_hba.conf - Docker network uchun trust
# Bu faqat ICHKI Docker network uchun, tashqaridan kira olmaydi
RUN echo "#!/bin/bash" > /docker-entrypoint-initdb.d/init-hba.sh && \
    echo 'echo "host all all 172.16.0.0/12 trust" >> /var/lib/postgresql/data/pg_hba.conf' >> /docker-entrypoint-initdb.d/init-hba.sh && \
    echo 'echo "host all all 192.168.0.0/16 trust" >> /var/lib/postgresql/data/pg_hba.conf' >> /docker-entrypoint-initdb.d/init-hba.sh && \
    chmod +x /docker-entrypoint-initdb.d/init-hba.sh

# Password sync script - har safar ishga tushganda
COPY sync-password.sh /usr/local/bin/sync-password.sh
RUN chmod +x /usr/local/bin/sync-password.sh

# Custom entrypoint
COPY docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-wrapper.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-wrapper.sh"]
CMD ["postgres"]
