class PrintABC {
    private int state = 0; // 0: 输出a, 1: 输出b, 2: 输出c
    private int n;

    public PrintABC(int n) {
        this.n = n;
    }

    public void printA() throws InterruptedException {
        for (int i = 0; i < n; i++) {
            synchronized (this) {
                while (state % 3 != 0) {
                    wait();
                }
                System.out.print("a");
                state++;
                notifyAll();
            }
        }
    }

    public void printB() throws InterruptedException {
        for (int i = 0; i < n; i++) {
            synchronized (this) {
                while (state % 3 != 1) {
                    wait();
                }
                System.out.print("b");
                state++;
                notifyAll();
            }
        }
    }

    public void printC() throws InterruptedException {
        for (int i = 0; i < n; i++) {
            synchronized (this) {
                while (state % 3 != 2) {
                    wait();
                }
                System.out.print("c");
                state++;
                notifyAll();
            }
        }
    }
}

// 启动方式
public class Demo {
    public static void main(String[] args) {
        PrintABC printer = new PrintABC(5); // 输出5次abc
        new Thread(() -> {
            try { printer.printA(); } catch (InterruptedException e) {}
        }).start();
        new Thread(() -> {
            try { printer.printB(); } catch (InterruptedException e) {}
        }).start();
        new Thread(() -> {
            try { printer.printC(); } catch (InterruptedException e) {}
        }).start();
    }
}