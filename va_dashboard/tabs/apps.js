var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');

var Apps = React.createClass({
    getInitialState: function () {
        return {status: 'none', progress: 0, hosts: []};
    },

    componentDidMount: function () {
        var me = this;
        Network.get('/api/hosts', this.props.auth.token).done(function (data) {
            me.setState({hosts: data.hosts});
        });
    },

    render: function () {
        var statusColor, statusDisplay, statusMessage;

        if(this.state.status == 'launching'){
            statusColor = 'yellow';
            statusDisplay = 'block';
            statusMessage = 'Launching... ' + this.state.progress + '%';
        }else if(this.state.status == 'launched'){
            statusColor = 'green';
            statusDisplay = 'block';
            statusMessage = 'Launched successfully!';
        }else {
            statusDisplay = 'none';
        }

        var host_rows = this.state.hosts.map(function(host) {
            return <option key = {host.name}>{host.name}</option>
        });

        return (
            <div>
                <h1>Launch new app</h1>
                <form onSubmit={this.onSubmit} className='form-horizontal'>
                    <div className='form-group'>
                    <select>
                        {host_rows}
                    </select> <br/>
                    <select>
                        <option>samba.sls</option>
                    </select>
                    <input placeholder='Instance name' ref='name'/> <br/>
                    <button>Launch</button>
                    <div style={{width: '100%', padding: 10, borderRadius: 5, background: statusColor, display: statusDisplay}}>
                        {statusMessage}
                    </div>
                    </div>
                </form>
            </div>
        );
    },
    onSubmit: function(e) {
        e.preventDefault();
        var me = this;
        this.setState({status: 'launching', progress: 0});
        interval = setInterval(function(){
            if(me.state.status == 'launching' && me.state.progress <= 80){
                var newProgress = me.state.progress + 10;
                me.setState({progress: newProgress})
            }else{
                clearInterval(interval);
            }
        }, 10000);
        var data = {name: this.refs.name.value};
        Network.post('/api/apps', this.props.auth.token, data).done(function(data) {
            me.setState({status: 'launched'});
        });
    }
});

Apps = connect(function(state){
    return {auth: state.auth};
})(Apps);

module.exports = Apps;
