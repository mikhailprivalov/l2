const io = require('socket.io')(8822);

io.on('connection', (socket) => {
    socket.on('results_save', function (data) {
        socket.broadcast.emit('results_save', data);
    });
    socket.on('result_confirm', function (data) {
        socket.broadcast.emit('result_confirm', data);
    });
    socket.on('ping', function (data) {
        console.log('ping', data)
    });
});
