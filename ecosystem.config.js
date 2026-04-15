module.exports = {
  apps: [
    {
      name: 'permessi-asl',
      script: 'venv/bin/gunicorn',
      args: '--bind 0.0.0.0:3002 --workers 2 --timeout 120 run:app',
      interpreter: 'none',
      cwd: __dirname,
      watch: false,
      autorestart: true,
      restart_delay: 5000,
    },
  ],
};
