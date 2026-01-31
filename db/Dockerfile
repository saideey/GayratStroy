FROM postgres:15-alpine

# Custom pg_hba.conf - Docker network uchun trust
COPY pg_hba.conf /etc/postgresql/pg_hba.conf
RUN chmod 644 /etc/postgresql/pg_hba.conf

# Password sync script
COPY docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-wrapper.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-wrapper.sh"]
CMD ["postgres"]
