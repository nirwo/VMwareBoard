const app = Vue.createApp({
    data() {
        return {
            vms: [],
            darkMode: false
        }
    },
    methods: {
        async fetchVMs() {
            try {
                const response = await axios.get('http://localhost:5000/api/vms');
                this.vms = response.data;
            } catch (error) {
                console.error('Error fetching VMs:', error);
            }
        },
        async powerOnOff(vm) {
            // Implement power on/off logic here
            console.log(`Power ${vm.power_state === 'poweredOn' ? 'off' : 'on'} ${vm.name}`);
        },
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
        }
    },
    mounted() {
        this.fetchVMs();
    }
});

app.mount('#app');
