var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');

var Overview = React.createClass({
    render: function() {
        var appblocks = [['Directory', 'fa-group'], ['Monitoring', 'fa-heartbeat'],
            ['Backup', 'fa-database'], ['OwnCloud', 'fa-cloud'], ['Fileshare', 'fa-folder-open'],
            ['Email', 'fa-envelope']];
        appblocks = appblocks.map(function(d){
            return (
                <div key={d[0]} className='app-block'>
                    <div className='icon-wrapper'>
                        <i className={'fa ' + d[1]} />
                    </div>
                    <div className='name-wrapper'>
                        <h1>{d[0]}</h1>
                    </div>
                    <div className='clearfix' />
                </div>
            );
        });
        return (
            <div>
                {appblocks}
                <div style={{clear: 'both'}} />
            </div>);
    }
});

Overview = connect(function(state) {
    return {auth: state.auth};
})(Overview);

module.exports = Overview;
