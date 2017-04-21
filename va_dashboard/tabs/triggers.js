var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
var connect = require('react-redux').connect;

var Triggers = React.createClass({
    getInitialState: function () {
        return {triggers: [], operators: {'lt': '<', 'gt': '>', 'ge': '>=', 'le': '<='}};
    },
    getCurrentTriggers: function () {
        var me = this;
        Network.get('/api/triggers', this.props.auth.token).done(function (data) {
            me.setState({triggers: data["va-clc"]});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentDidMount: function () {
        this.getCurrentTriggers();
    },
    executeAction: function (rowNum, evtKey) {
        var trigger = this.state.triggers[rowNum];
        var me = this;
        switch (evtKey) {
            case "edit":
                this.props.dispatch({type: 'OPEN_MODAL', args: trigger});
                break;
            case "delete":
                break;
            default:
                break;
        }
    },
    openModal: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },
    addTrigger: function (service, status, conditions, target, actions) {
        this.setState({active: this.state.triggers.concat([{"service": service, "status": status, "conditions": conditions, "target": target, "actions": actions}])});
    },
    render: function () {
        var me = this;
        var trigger_rows = this.state.triggers.map(function(trigger, i) {
            var conditions = trigger.conditions.map(function(c, j) {
                return (
                    <div key={j}>{c.func}</div>
                );
            });
            var actions = trigger.actions.map(function(a, j) {
                return (
                    <div key={j}>{a.func}</div>
                );
            });
            var actionBtn = (
                <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {me.executeAction.bind(me, i)}>
                    <Bootstrap.MenuItem key="edit" eventKey="edit">Edit</Bootstrap.MenuItem>
                    <Bootstrap.MenuItem key="delete" eventKey="delete">Delete</Bootstrap.MenuItem>
                </Bootstrap.DropdownButton>
            );
            return (
                <tr key={i}>
                    <td>{trigger.service}</td>
                    <td>{trigger.status}</td>
                    <td>{conditions}</td>
                    <td>Terminal</td>
                    <td>{actions}</td>
                    <td>{actionBtn}</td>
                </tr>
            );
        });
        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal, alert: state.alert};
        })(Modal);
        var TriggerFormRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(TriggerForm);

        return (
            <div>
                <TriggerFormRedux />
                <Bootstrap.PageHeader>List triggers</Bootstrap.PageHeader>
                <Bootstrap.Button type="button" bsStyle='default' className="pull-right margina" onClick={this.openModal}>
                    <Bootstrap.Glyphicon glyph='plus' />
                    Add trigger
                </Bootstrap.Button>
                <ModalRedux addTrigger = {this.addTrigger} />
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                        <td>Service</td>
                        <td>Status</td>
                        <td>Conditions</td>
                        <td>Target</td>
                        <td>Actions</td>
                        <td></td>
                        </tr>
                    </thead>
                    <tbody>
                        {trigger_rows}
                    </tbody>
                </Bootstrap.Table>
            </div>
        );
    }
});

var Modal = React.createClass({
    getInitialState: function () {
        var values = {"service": "", "status": "", "conditions": "", "target": "", "actions": ""};
        var args = this.props.modal.args;
        if('service' in args){
            for(var key in args){
                values[key] = args[key];
            }
        }
        return values;
    },

    open: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },

    action: function(e) {
        console.log(e.target);
        console.log(this.refs.forma);
        console.log(ReactDOM.findDOMNode(this.refs.forma).elements);
        var elements = ReactDOM.findDOMNode(this.refs.forma).elements;
        var data = {};
        for(i=0; i<elements.length; i++){
            data[elements[i].name] = elements[i].value;
        }
        console.log(data);
        var me = this;
        Network.post("/api/apps/add_trigger", this.props.auth.token, data).done(function(d) {
            if(d === true){
                me.props.addTrigger(data['service'], data['status'], data['conditions'], data['target'], data['actions']);
            }
            me.props.dispatch({type: 'CLOSE_MODAL'});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    render: function () {
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>Create Trigger</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <div className="left">
                    <Bootstrap.Form ref="forma">
                        <Bootstrap.FormControl id="service" key="service" name="service" componentClass="select" value={this.state["service"]}>
                            <option value="CPU">CPU</option>
                            <option value="Memory">Memory</option>
                            <option value="CPUSize">CPUSize</option>
                            <option value="MemorySize">MemorySize</option>
                            <option value="Memory">Memory</option>
                        </Bootstrap.FormControl>
                        <Bootstrap.FormControl id="status" key="status" name="status" componentClass="select" value={this.state["status"]}>
                            <option value="CRITICAL">CRITICAL</option>
                            <option value="OK">OK</option>
                            <option value="WARNING">WARNING</option>
                        </Bootstrap.FormControl>
                        <Bootstrap.FormControl type='text' name="conditions" placeholder="Conditions" value={this.state["conditions"]} />
                        <Bootstrap.FormControl type='text' name="target" value="Terminal" disabled />
                        <Bootstrap.FormControl type='text' name="actions" placeholder="Actions" value={this.state["actions"]} />
                    </Bootstrap.Form>
                </div>
                <div className="right">
                    <h3>Fill the form to add new trigger</h3>
                    <div></div>
                </div>
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
              <Bootstrap.Button onClick={this.close}>Cancel</Bootstrap.Button>
              <Bootstrap.Button onClick={this.action} bsStyle = "primary">Add trigger</Bootstrap.Button>
            </Bootstrap.Modal.Footer>

        </Bootstrap.Modal>
        );
    }
});

var TriggerForm = React.createClass({
    getInitialState: function () {
        return {CPU: {name: 'CPU', min: 50, max: 100, min_size: 2, max_size: 8, w_val: 0, c_val: 0, size: 0}, Memory: {name: 'Memory', min: 50, max: 100, min_size: 3000, max_size: 16000, w_val: 0, c_val: 0, size: 0}, TotalUsers: {name: 'Users', min: 0, max: 200, min_size: 50, max_size: 200, w_val: 0, c_val: 0, size: 0}, severity: ['w_val', 'c_val', 'size']};
    },
    getTriggerVals: function () {
        var me = this;
        Network.get('/api/evo/get_all_icinga_services', this.props.auth.token).done(function (data) {
            var cpu = Object.assign({}, me.state.CPU, data.CPU);
            var mem = Object.assign({}, me.state.Memory, data.Memory);
            var usr = Object.assign({}, me.state.TotalUsers, data.TotalUsers);
            me.setState({CPU: cpu, Memory: mem, TotalUsers: usr});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentDidMount: function () {
        this.getTriggerVals();
    },
    onChange: function(e) {
        var arr = e.target.id.split("_");
        var service = Object.assign({}, this.state[arr[0]]);
        service[this.state.severity[arr[1]]] = e.target.value;
        this.setState({[arr[0]]: service});
    },
    updateTriggerVals: function (e) {
        e.preventDefault();
        var me = this;
        var data = [];
        for(var key in this.state){
            if(key !== 'severity'){
                data.push({service: key, severity : "WARNING", value: this.state[key].w_val});
                data.push({service: key, severity : "CRITICAL", value: this.state[key].c_val});
                data.push({service: key, severity : "MAXIMUM", value: this.state[key].size});
            }
        }
        console.log(data);
        Network.post('/api/evo/change_icinga_services', this.props.auth.token, {services: data}).done(function (data) {
            console.log("success");
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    render: function () {
        return (
            <div>
                <Bootstrap.PageHeader>Change thresholds</Bootstrap.PageHeader>
                <form onSubmit={this.updateTriggerVals}>
                    <table className="threshold-tbl">
                        <tr>
                            <th></th>
                            <th>Warning</th>
                            <th>Critical</th>
                            <th>Maximum</th>
                        </tr>
                        <tr>
                            <td>CPU</td>
                            <td><input type='number' min={this.state.CPU.min} max={this.state.CPU.max} id="CPU_0" key="CPU_0" value={this.state.CPU.w_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={this.state.CPU.min} max={this.state.CPU.max} id="CPU_1" key="CPU_1" value={this.state.CPU.c_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={this.state.CPU.min_size} max={this.state.CPU.max_size} id="CPU_2" key="CPU_2" value={this.state.CPU.size} onChange={this.onChange} /></td>
                        </tr>
                        <tr>
                            <td>Memory</td>
                            <td><input type='number' min={this.state.Memory.min} max={this.state.Memory.max} id="Memory_0" key="Memory_0" value={this.state.Memory.w_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={this.state.Memory.min} max={this.state.Memory.max} id="Memory_1" key="Memory_1" value={this.state.Memory.c_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={this.state.Memory.min_size} max={this.state.Memory.max_size} id="Memory_2" key="Memory_2" value={this.state.Memory.size} onChange={this.onChange} /></td>
                        </tr>
                        <tr>
                            <td>Users</td>
                            <td><input type='number' min={this.state.TotalUsers.min} max={this.state.TotalUsers.max} id="TotalUsers_0" key="TotalUsers_0" value={this.state.TotalUsers.w_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={this.state.TotalUsers.min} max={this.state.TotalUsers.max} id="TotalUsers_1" key="TotalUsers_1" value={this.state.TotalUsers.c_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={0} max={this.state.TotalUsers.max_size} id="TotalUsers_2" key="TotalUsers_2" value={this.state.TotalUsers.size} onChange={this.onChange} /></td>
                        </tr>
                    </table>
                    <input type="submit" className="btn btn-primary" value="Apply changes" />
                </form>
            </div>
        );
    }
});

Triggers = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Triggers);

module.exports = Triggers;

