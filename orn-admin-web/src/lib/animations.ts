import anime from "animejs/lib/anime.es.js";

export const fadeInScale = (element: Element) => {
  return anime({
    targets: element,
    scale: [0.9, 1],
    opacity: [0, 1],
    duration: 400,
    easing: "easeOutCubic",
  });
};

export const pulseAnimation = (element: Element) => {
  return anime({
    targets: element,
    scale: [1, 1.05, 1],
    duration: 600,
    easing: "easeInOutQuad",
    loop: true,
  });
};

export const progressAnimation = (element: Element, progress: number) => {
  return anime({
    targets: element,
    width: `${progress}%`,
    duration: 800,
    easing: "easeInOutQuart",
  });
};

export const staggerChildren = (container: Element, delay = 50) => {
  return anime({
    targets: container.children,
    translateY: [20, 0],
    opacity: [0, 1],
    duration: 600,
    delay: anime.stagger(delay),
    easing: "easeOutExpo",
  });
};

export const shimmerAnimation = (element: Element) => {
  return anime({
    targets: element,
    backgroundPosition: ["200% 50%", "-100% 50%"],
    duration: 2500,
    loop: true,
    easing: "linear",
  });
};

export const notificationBell = (element: Element) => {
  return anime({
    targets: element,
    rotateZ: [-10, 10, -10, 0],
    duration: 400,
    easing: "easeInOutBack",
  });
};

// Framer Motion variants
export const tableRowVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.3,
      ease: "easeOut",
    },
  }),
  exit: { opacity: 0, y: -20 },
};

export const modalVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: {
      duration: 0.2,
    },
  },
};

export const cardVariants = {
  hover: {
    scale: 1.02,
    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
  tap: {
    scale: 0.98,
  },
};
