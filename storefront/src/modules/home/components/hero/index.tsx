import { Heading } from "@medusajs/ui"

const Hero = () => {
  return (
    <div className="relative h-[80vh] w-full overflow-hidden bg-zinc-950 flex items-center">
      {/* Background Studio Product Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-60 scale-105 transition-all duration-700"
        style={{ backgroundImage: "url('/hero-product.png')" }}
      />
      
      {/* Dark Radial Mask to blend corners and assure readability */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_20%,#09090b_90%)]" />
      <div className="absolute inset-0 bg-gradient-to-r from-zinc-950/90 via-zinc-950/40 to-transparent" />

      {/* Main Container */}
      <div className="content-container relative z-10 w-full">
        {/* Glassmorphic overlay card for B2B copywriting */}
        <div className="max-w-xl p-8 rounded-2xl border border-white/10 bg-zinc-950/40 backdrop-blur-md shadow-2xl flex flex-col gap-6 items-start">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-secondary bg-secondary/15 border border-secondary/20 shadow-[0_0_8px_var(--secondary-sdui)]">
            Catálogo Mayorista Exclusivo
          </span>
          <div>
            <Heading
              level="h1"
              className="text-4xl small:text-5xl font-bold tracking-tight text-white mb-2"
            >
              VibeCloud B2B
            </Heading>
            <Heading
              level="h2"
              className="text-lg small:text-xl font-normal text-zinc-300 leading-relaxed"
            >
              Abastecimiento inteligente y distribución premium a un clic.
            </Heading>
          </div>
          
          <button 
            type="button"
            className="px-6 py-3 rounded-xl font-medium text-white transition-all duration-300 hover:scale-[1.02] shadow-lg"
            style={{ 
              backgroundColor: "var(--primary-sdui)",
              boxShadow: "0 0 15px var(--primary-sdui)" 
            }}
          >
            Explorar Productos
          </button>
        </div>
      </div>
    </div>
  )
}

export default Hero

