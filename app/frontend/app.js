const app = Vue.createApp({
    data() {
        return {
            vms: [],
            darkMode: false,
            loading: false,
            error: null,
            selectedVM: null,
            snapshotName: '',
            snapshotDescription: '',
            selectedTab: 'general',
            isConnected: false,
            vcenterHost: '',
            vcenterUser: '',
            vcenterPassword: ''
        }
    },
    methods: {
        async connectToVCenter() {
            try {
                const response = await axios.post('http://localhost:5079/api/vcconnect', {
                    host: this.vcenterHost,
                    user: this.vcenterUser,
                    password: this.vcenterPassword
                });
                if (response.data.status === 'success') {
                    this.isConnected = true;
                    this.error = null;
                    this.fetchVMs();
                }
            } catch (error) {
                console.error('Error connecting to vCenter:', error);
                this.error = 'Failed to connect to vCenter. Please check your credentials and try again.';
            }
        },
        async disconnectFromVCenter() {
            try {
                await axios.post('http://localhost:5079/api/vcdisconnect');
                this.isConnected = false;
                this.vms = [];
                this.error = null;
            } catch (error) {
                console.error('Error disconnecting from vCenter:', error);
                this.error = 'Failed to disconnect from vCenter.';
            }
        },
        async checkVCenterStatus() {
            try {
                const response = await axios.get('http://localhost:5079/api/vcstatus');
                this.isConnected = response.data.status === 'connected';
                if (this.isConnected) {
                    this.vcenterHost = response.data.host;
                    this.fetchVMs();
                }
            } catch (error) {
                console.error('Error checking vCenter status:', error);
                this.error = 'Failed to check vCenter connection status.';
            }
        },
        async fetchVMs() {
            if (!this.isConnected) return;
            
            this.loading = true;
            this.error = null;
            try {
                const response = await axios.get('http://localhost:5079/api/vms');
                this.vms = response.data;
            } catch (error) {
                console.error('Error fetching VMs:', error);
                this.error = 'Failed to fetch VMs. Please try again.';
            } finally {
                this.loading = false;
            }
        },
        async powerOnOff(vm) {
            const action = vm.power_state === 'poweredOn' ? 'off' : 'on';
            try {
                await axios.post(`http://localhost:5079/api/vm/${vm.name}/power`, { action });
                // Optimistic update
                vm.power_state = action === 'on' ? 'poweredOn' : 'poweredOff';
                // Refetch VMs after a short delay to ensure the change has propagated
                setTimeout(() => this.fetchVMs(), 2000);
            } catch (error) {
                console.error(`Error powering ${action} VM:`, error);
                alert(`Failed to power ${action} VM. Please try again.`);
            }
        },
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
        },
        selectVM(vm) {
            this.selectedVM = vm;
        },
        async createSnapshot() {
            try {
                await axios.post(`http://localhost:5079/api/vm/${this.selectedVM.name}/snapshot`, {
                    name: this.snapshotName,
                    description: this.snapshotDescription
                });
                alert('Snapshot creation initiated');
                this.snapshotName = '';
                this.snapshotDescription = '';
                setTimeout(() => this.fetchVMs(), 2000);
            } catch (error) {
                console.error('Error creating snapshot:', error);
                alert('Failed to create snapshot. Please try again.');
            }
        },
        async revertSnapshot(snapshot) {
            try {
                await axios.post(`http://localhost:5079/api/vm/${this.selectedVM.name}/snapshot/${snapshot.id}/revert`);
                alert('Revert to snapshot initiated');
                setTimeout(() => this.fetchVMs(), 2000);
            } catch (error) {
                console.error('Error reverting snapshot:', error);
                alert('Failed to revert snapshot. Please try again.');
            }
        },
        async deleteSnapshot(snapshot) {
            try {
                await axios.delete(`http://localhost:5079/api/vm/${this.selectedVM.name}/snapshot/${snapshot.id}`);
                alert('Snapshot deletion initiated');
                setTimeout(() => this.fetchVMs(), 2000);
            } catch (error) {
                console.error('Error deleting snapshot:', error);
                alert('Failed to delete snapshot. Please try again.');
            }
        }
    },
    mounted() {
        this.checkVCenterStatus();
        // Set up polling to refresh VM data every 30 seconds if connected
        setInterval(() => {
            if (this.isConnected) {
                this.fetchVMs();
            }
        }, 30000);
    }
});

app.mount('#app');
