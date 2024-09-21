const app = Vue.createApp({
    data() {
        return {
            vms: [],
            darkMode: false,
            loading: false,
            error: null
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
        }
    },
    mounted() {
        this.fetchVMs();
        // Set up polling to refresh VM data every 30 seconds
        setInterval(this.fetchVMs, 30000);
    }
});

app.mount('#app');
