/**
 * VMware vCenter Management Frontend Application
 * 
 * This Vue.js application provides a user interface for managing VMware vCenter environments.
 * It allows users to connect to a vCenter server, view and manage virtual machines, and perform
 * various operations such as power management and snapshot creation.
 * 
 * Author: Your Name
 * Date: September 21, 2024
 */

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
        /**
         * Connect to the vCenter server using the provided credentials.
         */
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
        /**
         * Disconnect from the vCenter server.
         */
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
        /**
         * Check the current vCenter connection status.
         */
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
        /**
         * Fetch the list of virtual machines from the vCenter server.
         */
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
        /**
         * Power on or off a virtual machine.
         * @param {Object} vm - The virtual machine object.
         */
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
        /**
         * Toggle dark mode for the application.
         */
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
        },
        /**
         * Select a virtual machine for detailed view.
         * @param {Object} vm - The virtual machine object.
         */
        selectVM(vm) {
            this.selectedVM = vm;
        },
        /**
         * Create a snapshot of the selected virtual machine.
         */
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
        /**
         * Revert the selected virtual machine to a specific snapshot.
         * @param {Object} snapshot - The snapshot object.
         */
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
        /**
         * Delete a specific snapshot of the selected virtual machine.
         * @param {Object} snapshot - The snapshot object.
         */
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
        // Check vCenter status when the application is mounted
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
