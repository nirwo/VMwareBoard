const app = Vue.createApp({
    data() {
        return {
            vms: [],
            darkMode: false,
            loading: false,
            error: null,
            selectedVM: null,
            snapshotName: '',
            snapshotDescription: ''
        }
    },
    methods: {
        async fetchVMs() {
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
        this.fetchVMs();
        // Set up polling to refresh VM data every 30 seconds
        setInterval(this.fetchVMs, 30000);
    }
});

app.mount('#app');
